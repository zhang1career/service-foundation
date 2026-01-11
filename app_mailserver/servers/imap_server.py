"""
IMAP server implementation

This module implements a basic IMAP server to provide email access
and attachment retrieval from OSS.
"""
import asyncio
import logging
from asgiref.sync import sync_to_async
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Optional, List

from app_mailserver.config import get_app_config
from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.repos import (
    get_account_by_username,
    get_mailbox_by_account_and_path,
    get_mailboxes_by_account,
    get_messages_by_mailbox,
    count_messages_by_mailbox,
    count_unread_messages_by_mailbox,
    update_message_read_status,
    get_attachments_by_message,
)
from app_mailserver.services.mail_storage_service import MailStorageService
from common.enums.content_type_enum import ContentTypeEnum

logger = logging.getLogger(__name__)


class IMAPHandler:
    """IMAP protocol handler"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.storage_service = MailStorageService()
        self.account: Optional[MailAccount] = None
        self.selected_mailbox: Optional[Mailbox] = None
        self.tag_counter = 0
        self.authenticated = False

    async def handle_client(self):
        """Handle IMAP client connection"""
        try:
            # Send greeting
            await self.send_response('* OK IMAP server ready')

            # Process commands
            while True:
                line = await self.reader.readline()
                if not line:
                    break

                line = line.decode('utf-8', errors='replace').strip()
                if not line:
                    continue

                await self.process_command(line)

        except Exception as e:
            logger.exception(f"[handle_client] Error handling client: {e}")
        finally:
            self.writer.close()
            await self.writer.wait_closed()

    def _parse_imap_args(self, arg_string: str) -> List[str]:
        """
        Parse IMAP command arguments, handling quoted strings
        
        Args:
            arg_string: Argument string after command name
            
        Returns:
            List of parsed arguments
        """
        args = []
        current_arg = []
        in_quotes = False
        quote_char = None
        i = 0

        while i < len(arg_string):
            char = arg_string[i]

            if char in ('"', "'") and (i == 0 or arg_string[i - 1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                # Don't include quote in result
            elif char == ' ' and not in_quotes:
                if current_arg:
                    args.append(''.join(current_arg))
                    current_arg = []
            else:
                current_arg.append(char)

            i += 1

        # Add last argument
        if current_arg:
            args.append(''.join(current_arg))

        return args

    async def process_command(self, line: str):
        """Process IMAP command"""
        try:
            # Parse command
            parts = line.split(None, 1)
            if not parts:
                await self.send_response('* BAD Empty command')
                return

            tag = parts[0]

            if len(parts) < 2:
                command = ''
                args = []
            else:
                remaining = parts[1]
                # Find command (first word)
                first_space = remaining.find(' ')
                if first_space == -1:
                    command = remaining.upper()
                    args = []
                else:
                    command = remaining[:first_space].upper()
                    arg_string = remaining[first_space + 1:]
                    args = self._parse_imap_args(arg_string)

            # Route command
            if command == 'CAPABILITY':
                await self.handle_capability(tag)
            elif command == 'LOGIN':
                await self.handle_login(tag, args)
            elif command == 'SELECT' or command == 'EXAMINE':
                await self.handle_select(tag, args)
            elif command == 'LIST':
                await self.handle_list(tag, args)
            elif command == 'FETCH':
                await self.handle_fetch(tag, args)
            elif command == 'SEARCH':
                await self.handle_search(tag, args)
            elif command == 'STORE':
                await self.handle_store(tag, args)
            elif command == 'UID':
                await self.handle_uid(tag, args)
            elif command == 'LOGOUT':
                await self.handle_logout(tag)
            else:
                await self.send_response(f'{tag} BAD Unknown command, command={command}, args={args}')

        except Exception as e:
            logger.exception(f"[process_command] Error processing command: {e}")
            await self.send_response('* BAD Command error')

    async def handle_capability(self, tag: str):
        """Handle CAPABILITY command"""
        capabilities = [
            'IMAP4rev1',
            'UIDPLUS',
            'ENABLE',
            'SASL-IR',
            'AUTH=PLAIN'
        ]
        await self.send_response(f'* CAPABILITY {" ".join(capabilities)}')
        await self.send_response(f'{tag} OK Capability completed')

    async def handle_login(self, tag: str, args: List[str]):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[handle_login] args: {args}")

        """Handle LOGIN command"""
        if len(args) < 2:
            await self.send_response(f'{tag} BAD Login command requires username and password')
            return

        # Remove quotes from username and password if present (IMAP string format)
        username = args[0].strip('"\'')
        password = args[1].strip('"\'')

        try:
            account = await sync_to_async(get_account_by_username)(username, is_active=True)

            if not account:
                await self.send_response(f'{tag} NO Login failed: account not found')
                logger.warning(f"[handle_login] Account not found: {username}")
                return

            # Check password: account.password must exist and match
            if not account.password:
                await self.send_response(f'{tag} NO Login failed: account has no password set')
                logger.warning(f"[handle_login] Account has no password: {username}")
                return

            if account.password == password:
                self.account = account
                self.authenticated = True
                await self.send_response(f'{tag} OK Login successful')
                logger.info(f"[handle_login] User logged in: {username}")
            else:
                await self.send_response(f'{tag} NO Login failed: authentication failed')
                logger.warning(f"[handle_login] Login failed for: {username} (password mismatch)")

        except Exception as e:
            logger.exception(f"[handle_login] Error during login: {e}")
            await self.send_response(f'{tag} NO Login failed: {str(e)}')

    async def handle_select(self, tag: str, args: List[str]):
        """Handle SELECT or EXAMINE command"""
        if not self.authenticated:
            await self.send_response(f'{tag} NO Not authenticated')
            return

        if not args:
            await self.send_response(f'{tag} BAD Mailbox name required')
            return

        mailbox_name = args[0].strip('"')

        try:
            mailbox = await sync_to_async(get_mailbox_by_account_and_path)(self.account.id, mailbox_name)

            if not mailbox:
                await self.send_response(f'{tag} NO Mailbox does not exist')
                return

            self.selected_mailbox = mailbox

            # Get message count
            message_count = await sync_to_async(count_messages_by_mailbox)(mailbox.id)
            recent_count = await sync_to_async(count_unread_messages_by_mailbox)(mailbox.id)

            # Send mailbox status
            await self.send_response(f'* {message_count} EXISTS')
            await self.send_response(f'* {recent_count} RECENT')
            await self.send_response(f'* OK [UIDVALIDITY 1] UIDs valid')
            await self.send_response(f'* OK [UIDNEXT {message_count + 1}] Predicted next UID')
            await self.send_response(f'* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)')
            await self.send_response(f'* OK [PERMANENTFLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)] Limited')
            await self.send_response(f'{tag} OK [READ-WRITE] SELECT completed')

        except Exception as e:
            logger.exception(f"[handle_select] Error selecting mailbox: {e}")
            await self.send_response(f'{tag} NO Select failed: {str(e)}')

    async def handle_list(self, tag: str, args: List[str]):
        """Handle LIST command"""
        if not self.authenticated:
            await self.send_response(f'{tag} NO Not authenticated')
            return

        try:
            mailboxes = await sync_to_async(get_mailboxes_by_account)(self.account.id)

            for mailbox in mailboxes:
                # Format: * LIST (\HasNoChildren) "/" "INBOX"
                await self.send_response(f'* LIST (\\HasNoChildren) "/" "{mailbox.path}"')

            await self.send_response(f'{tag} OK List completed')

        except Exception as e:
            logger.exception(f"[handle_list] Error listing mailboxes: {e}")
            await self.send_response(f'{tag} NO List failed: {str(e)}')

    async def handle_fetch(self, tag: str, args: List[str]):
        """Handle FETCH command"""
        if not self.authenticated or not self.selected_mailbox:
            await self.send_response(f'{tag} NO Not authenticated or no mailbox selected')
            return

        if len(args) < 2:
            await self.send_response(f'{tag} BAD FETCH command requires sequence and data items')
            return

        sequence = args[0]
        data_items = ' '.join(args[1:])

        try:
            # Get messages
            messages = await sync_to_async(get_messages_by_mailbox)(
                self.selected_mailbox.id,
                order_by='mt'
            )

            # Parse sequence (simplified: assume single message number)
            if sequence.isdigit():
                msg_num = int(sequence)
                if msg_num < 1 or msg_num > len(messages):
                    await self.send_response(f'{tag} NO Invalid message number')
                    return
                messages = [messages[msg_num - 1]]
            elif sequence == '*':
                messages = [messages[-1]] if messages else []
            else:
                await self.send_response(f'{tag} BAD Invalid sequence')
                return

            # Fetch message data
            for msg in messages:
                await self.send_fetch_response(msg, data_items)

            await self.send_response(f'{tag} OK Fetch completed')

        except Exception as e:
            logger.exception(f"[handle_fetch] Error fetching message: {e}")
            await self.send_response(f'{tag} NO Fetch failed: {str(e)}')

    async def send_fetch_response(self, message: MailMessage, data_items: str, sequence_num: Optional[int] = None, include_uid: bool = False):
        """
        Send FETCH response for a message
        
        Args:
            message: MailMessage object
            data_items: Data items to include in response
            sequence_num: Optional sequence number to use in response (defaults to message.id)
            include_uid: Whether to include UID in the response (for UID FETCH)
        """
        try:
            # Use provided sequence number or message.id as default
            seq = sequence_num if sequence_num is not None else message.id
            
            # Build response based on data items
            response_parts = []

            if 'BODY[]' in data_items or 'RFC822' in data_items:
                # Full message
                body = await self._build_rfc822_message(message)
                response_parts.append(f'BODY[] {{{len(body)}}}')
                if include_uid:
                    response_parts.insert(0, f'UID {message.id}')
                await self.send_response(f'* {seq} FETCH ({", ".join(response_parts)})')
                await self.send_data(body)
            elif 'BODYSTRUCTURE' in data_items:
                # Body structure
                structure = self._build_body_structure(message)
                response_parts.append(f'BODYSTRUCTURE {structure}')
                if include_uid:
                    response_parts.insert(0, f'UID {message.id}')
                await self.send_response(f'* {seq} FETCH ({", ".join(response_parts)})')
            else:
                # Basic headers
                flags = []
                if message.is_read:
                    flags.append('\\Seen')
                if message.is_flagged:
                    flags.append('\\Flagged')

                flags_str = ' '.join(flags) if flags else '()'
                response_parts.append(f'FLAGS {flags_str}')
                # Convert UNIX timestamp (milliseconds) to datetime for INTERNALDATE
                date_dt = datetime.utcfromtimestamp(message.mt / 1000.0)
                response_parts.append(f'INTERNALDATE "{date_dt.strftime("%d-%b-%Y %H:%M:%S +0000")}"')
                response_parts.append(f'RFC822.SIZE {message.size}')
                
                # Include UID at the beginning if requested
                if include_uid:
                    response_parts.insert(0, f'UID {message.id}')

                await self.send_response(f'* {seq} FETCH ({", ".join(response_parts)})')

        except Exception as e:
            logger.exception(f"[send_fetch_response] Error sending fetch response: {e}")

    async def _build_rfc822_message(self, message: MailMessage) -> str:
        """Build RFC822 formatted message"""
        lines = [f'Message-ID: {message.message_id}', f'From: {message.from_address}', f'To: {message.to_addresses}']
        if message.cc_addresses:
            lines.append(f'Cc: {message.cc_addresses}')
        lines.append(f'Subject: {message.subject}')
        # Convert UNIX timestamp (milliseconds) to datetime for Date header
        date_dt = datetime.utcfromtimestamp(message.mt / 1000.0)
        lines.append(f'Date: {formatdate(date_dt.timestamp())}')
        lines.append('MIME-Version: 1.0')
        lines.append('Content-Type: multipart/mixed; boundary="boundary"')
        lines.append('')
        lines.append('--boundary')
        if message.text_body:
            lines.append('Content-Type: text/plain; charset=utf-8')
            lines.append('')
            lines.append(message.text_body)
        if message.html_body:
            lines.append('--boundary')
            lines.append('Content-Type: text/html; charset=utf-8')
            lines.append('')
            lines.append(message.html_body)
        # Add attachments
        attachments = await sync_to_async(get_attachments_by_message)(message.id)
        for attachment in attachments:
            # Convert enum ID to MIME type string
            try:
                content_type_enum = ContentTypeEnum(attachment.content_type)
                mime_type = content_type_enum.to_mime_type()
            except (ValueError, AttributeError):
                # Fallback to default if enum value is invalid
                mime_type = 'application/octet-stream'

            lines.append('--boundary')
            lines.append(f'Content-Type: {mime_type}')
            lines.append(f'Content-Disposition: {attachment.content_disposition}; filename="{attachment.filename}"')
            lines.append('Content-Transfer-Encoding: base64')
            lines.append('')
            # Note: In real implementation, would fetch and encode attachment data
            lines.append('[Attachment data]')
        lines.append('--boundary--')
        return '\r\n'.join(lines)

    def _build_body_structure(self, message: MailMessage) -> str:
        """Build BODYSTRUCTURE response"""
        # Simplified body structure
        parts = []
        if message.text_body:
            parts.append('("text" "plain" ("charset" "utf-8") NIL NIL "7bit" 0 0)')
        if message.html_body:
            parts.append('("text" "html" ("charset" "utf-8") NIL NIL "7bit" 0 0)')
        return f'({" ".join(parts) if parts else "NIL"})'

    async def handle_search(self, tag: str, args: List[str]):
        """Handle SEARCH command"""
        if not self.authenticated or not self.selected_mailbox:
            await self.send_response(f'{tag} NO Not authenticated or no mailbox selected')
            return

        try:
            messages = await sync_to_async(get_messages_by_mailbox)(
                self.selected_mailbox.id,
                order_by='date'
            )

            # Simple search: return all message IDs
            message_ids = [str(msg.id) for msg in messages]

            if message_ids:
                await self.send_response(f'* SEARCH {" ".join(message_ids)}')
            else:
                await self.send_response('* SEARCH')

            await self.send_response(f'{tag} OK Search completed')

        except Exception as e:
            logger.exception(f"[handle_search] Error searching: {e}")
            await self.send_response(f'{tag} NO Search failed: {str(e)}')

    async def handle_store(self, tag: str, args: List[str]):
        """Handle STORE command"""
        if not self.authenticated or not self.selected_mailbox:
            await self.send_response(f'{tag} NO Not authenticated or no mailbox selected')
            return

        if len(args) < 2:
            await self.send_response(f'{tag} BAD STORE command requires sequence and flags')
            return

        sequence = args[0]
        flags = ' '.join(args[1:])

        try:
            # Parse flags
            if '+FLAGS' in flags:
                # Add flags
                if '\\Seen' in flags:
                    await sync_to_async(update_message_read_status)(
                        self.selected_mailbox.id,
                        int(sequence),
                        is_read=True
                    )
            elif '-FLAGS' in flags:
                # Remove flags
                if '\\Seen' in flags:
                    await sync_to_async(update_message_read_status)(
                        self.selected_mailbox.id,
                        int(sequence),
                        is_read=False
                    )

            await self.send_response(f'{tag} OK Store completed')

        except Exception as e:
            logger.exception(f"[handle_store] Error storing flags: {e}")
            await self.send_response(f'{tag} NO Store failed: {str(e)}')

    async def handle_uid(self, tag: str, args: List[str]):
        """Handle UID command"""
        if not self.authenticated or not self.selected_mailbox:
            await self.send_response(f'{tag} NO Not authenticated or no mailbox selected')
            return

        if not args:
            await self.send_response(f'{tag} BAD UID command requires subcommand')
            return

        subcommand = args[0].upper()
        sub_args = args[1:]

        if subcommand == 'SEARCH':
            await self.handle_uid_search(tag, sub_args)
        elif subcommand == 'FETCH':
            await self.handle_uid_fetch(tag, sub_args)
        else:
            await self.send_response(f'{tag} BAD UID subcommand not supported: {subcommand}')

    def _parse_uid_sequence(self, uid_seq: str) -> List[int]:
        """
        Parse UID sequence (e.g., "2", "2:2", "2:5", "*")
        
        Args:
            uid_seq: UID sequence string
            
        Returns:
            List of UID integers, or empty list if invalid
        """
        if uid_seq == '*':
            # * means last UID (will be handled separately)
            return []
        
        if ':' in uid_seq:
            # Range format: "2:5" or "2:*"
            parts = uid_seq.split(':', 1)
            try:
                start_uid = int(parts[0])
                if parts[1] == '*':
                    # "2:*" means from 2 to the highest UID
                    return [start_uid, -1]  # Use -1 to indicate "*"
                else:
                    end_uid = int(parts[1])
                    # Return range as list
                    return list(range(start_uid, end_uid + 1))
            except ValueError:
                return []
        else:
            # Single UID
            try:
                return [int(uid_seq)]
            except ValueError:
                return []

    def _parse_imap_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse IMAP date format (dd-MMM-yyyy) to datetime (UTC)
        
        Args:
            date_str: Date string in IMAP format (e.g., "08-Jan-2026")
            
        Returns:
            datetime object in UTC or None if parsing fails
        """
        try:
            # IMAP date format: dd-MMM-yyyy (e.g., "08-Jan-2026")
            # Parse as UTC time (IMAP dates are typically in UTC)
            dt = datetime.strptime(date_str, '%d-%b-%Y')
            # Set to UTC timezone (mail timestamps are stored in UTC)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning(f"[_parse_imap_date] Failed to parse date: {date_str}")
            return None

    async def handle_uid_search(self, tag: str, args: List[str]):
        """Handle UID SEARCH command"""
        try:
            # Get all messages for the mailbox
            messages = await sync_to_async(get_messages_by_mailbox)(
                self.selected_mailbox.id,
                order_by='mt'
            )

            # Parse search criteria
            i = 0

            while i < len(args):
                criterion = args[i].upper()

                if criterion == 'SINCE':
                    # SINCE <date>: messages with date >= date
                    if i + 1 >= len(args):
                        await self.send_response(f'{tag} BAD SINCE requires a date')
                        return

                    date_str = args[i + 1]
                    since_date = self._parse_imap_date(date_str)
                    if since_date is None:
                        await self.send_response(f'{tag} BAD Invalid date format: {date_str}')
                        return

                    # Convert to timestamp (milliseconds) at start of the day
                    since_timestamp = int(since_date.timestamp() * 1000)

                    # Filter messages
                    filtered_messages = []
                    for msg in messages:
                        if msg.mt >= since_timestamp:
                            filtered_messages.append(msg)
                    messages = filtered_messages
                    i += 2

                elif criterion == 'UNSEEN':
                    # UNSEEN: messages that are not read
                    filtered_messages = []
                    for msg in messages:
                        if not msg.is_read:
                            filtered_messages.append(msg)
                    messages = filtered_messages
                    i += 1

                else:
                    # Unknown criterion, skip it
                    logger.warning(f"[handle_uid_search] Unknown search criterion: {criterion}")
                    i += 1

            # Extract UIDs (in this implementation, UID is the message ID)
            matching_uids = [str(msg.id) for msg in messages]

            # Send response
            if matching_uids:
                await self.send_response(f'* SEARCH {" ".join(matching_uids)}')
            else:
                await self.send_response('* SEARCH')

            await self.send_response(f'{tag} OK UID SEARCH completed')

        except Exception as e:
            logger.exception(f"[handle_uid_search] Error in UID SEARCH: {e}")
            await self.send_response(f'{tag} NO UID SEARCH failed: {str(e)}')

    async def handle_uid_fetch(self, tag: str, args: List[str]):
        """Handle UID FETCH command"""
        if not self.authenticated or not self.selected_mailbox:
            await self.send_response(f'{tag} NO Not authenticated or no mailbox selected')
            return

        if len(args) < 2:
            await self.send_response(f'{tag} BAD UID FETCH command requires UID sequence and data items')
            return

        uid_sequence = args[0]
        data_items = ' '.join(args[1:])

        try:
            # Get all messages for the mailbox
            messages = await sync_to_async(get_messages_by_mailbox)(
                self.selected_mailbox.id,
                order_by='mt'
            )

            # Parse UID sequence first to validate it (before checking if mailbox is empty)
            if uid_sequence == '*':
                # * means last message (if messages exist)
                if not messages:
                    await self.send_response(f'{tag} OK UID FETCH completed')
                    return
                matching_messages = [messages[-1]]
            else:
                uid_list = self._parse_uid_sequence(uid_sequence)
                if not uid_list:
                    await self.send_response(f'{tag} BAD Invalid UID sequence')
                    return

                # Check if mailbox is empty (after validating UID sequence)
                if not messages:
                    await self.send_response(f'{tag} OK UID FETCH completed')
                    return

                # Handle range with * (e.g., "2:*")
                if len(uid_list) == 2 and uid_list[1] == -1:
                    # Range from start_uid to highest UID
                    start_uid = uid_list[0]
                    matching_messages = [msg for msg in messages if msg.id >= start_uid]
                else:
                    # Find messages matching UIDs
                    uid_set = set(uid_list)
                    matching_messages = [msg for msg in messages if msg.id in uid_set]

            if not matching_messages:
                await self.send_response(f'{tag} OK UID FETCH completed')
                return

            # Create a mapping of message ID to sequence number (1-based index)
            msg_id_to_seq = {msg.id: idx + 1 for idx, msg in enumerate(messages)}

            # Fetch message data
            for msg in matching_messages:
                sequence_num = msg_id_to_seq.get(msg.id, msg.id)
                await self.send_fetch_response(msg, data_items, sequence_num=sequence_num, include_uid=True)

            await self.send_response(f'{tag} OK UID FETCH completed')

        except Exception as e:
            logger.exception(f"[handle_uid_fetch] Error in UID FETCH: {e}")
            await self.send_response(f'{tag} NO UID FETCH failed: {str(e)}')

    async def handle_logout(self, tag: str):
        """Handle LOGOUT command"""
        await self.send_response('* BYE IMAP server logging out')
        await self.send_response(f'{tag} OK Logout completed')
        self.writer.close()

    async def send_response(self, response: str):
        """Send IMAP response"""
        self.writer.write(f'{response}\r\n'.encode('utf-8'))
        await self.writer.drain()

    async def send_data(self, data: str):
        """Send data (for FETCH BODY[])"""
        self.writer.write(data.encode('utf-8'))
        await self.writer.drain()


class IMAPServer:
    """IMAP server wrapper"""

    def __init__(self):
        self.config = get_app_config()
        self.host = self.config.get('server_host', '0.0.0.0')
        self.port = self.config.get('imap_port', 143)
        self.server: Optional[asyncio.Server] = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle new client connection"""
        handler = IMAPHandler(reader, writer)
        await handler.handle_client()

    async def start(self):
        """Start IMAP server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            logger.info(f"[IMAPServer] Started IMAP server on {self.host}:{self.port}")

            async with self.server:
                await self.server.serve_forever()

        except Exception as e:
            logger.exception(f"[IMAPServer] Failed to start IMAP server: {e}")
            raise

    def stop(self):
        """Stop IMAP server"""
        if self.server:
            self.server.close()
            logger.info("[IMAPServer] Stopped IMAP server")
