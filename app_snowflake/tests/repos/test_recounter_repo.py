import sys
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from app_snowflake.consts.recounter_const import DEFAULT_RECOUNTER


class TestRecounterRepo(TestCase):

    databases = {'default', 'snowflake_rw'}

    def setUp(self):
        """Set up test fixtures"""
        self.datacenter_id = 1
        self.machine_id = 100
        self.timestamp = 1234567890000

    def test_create_recounter(self):
        """Test create_recounter function"""
        # Mock the Recounter model class
        mock_recounter_instance = Mock()
        mock_create = Mock(return_value=mock_recounter_instance)
        mock_using = Mock()
        mock_using.create = mock_create
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects
        
        # Create a mock module for the models
        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class
        
        # Inject mock module before importing
        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            # Clear any cached imports
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            with patch('app_snowflake.repos.recounter_repo.get_now_timestamp_ms', return_value=self.timestamp):
                from app_snowflake.repos.recounter_repo import create_recounter
                result = create_recounter(self.datacenter_id, self.machine_id)

        # Assert
        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_create.assert_called_once_with(
            dcid=self.datacenter_id,
            mid=self.machine_id,
            rc=DEFAULT_RECOUNTER,
            ct=self.timestamp,
            ut=self.timestamp,
        )
        self.assertEqual(result, mock_recounter_instance)

    def test_create_recounter_with_different_ids(self):
        """Test create_recounter with different datacenter and machine IDs"""
        mock_recounter_instance = Mock()
        mock_create = Mock(return_value=mock_recounter_instance)
        mock_using = Mock()
        mock_using.create = mock_create
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects
        test_dcid = 5
        test_mid = 500

        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class

        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            with patch('app_snowflake.repos.recounter_repo.get_now_timestamp_ms', return_value=self.timestamp):
                from app_snowflake.repos.recounter_repo import create_recounter
                result = create_recounter(test_dcid, test_mid)

        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_create.assert_called_once_with(
            dcid=test_dcid,
            mid=test_mid,
            rc=DEFAULT_RECOUNTER,
            ct=self.timestamp,
            ut=self.timestamp,
        )
        self.assertEqual(result, mock_recounter_instance)

    def test_update_recounter_with_recount(self):
        """Test update_recounter function with recount in data_dict"""
        new_timestamp = 9876543210000
        
        origin = Mock()
        origin.id = 1
        origin.dcid = self.datacenter_id
        origin.mid = self.machine_id
        origin.rc = 10
        origin.ct = self.timestamp

        data_dict = {"recount": 20}
        mock_update = Mock(return_value=1)  # update returns number of rows updated
        mock_filter = Mock()
        mock_filter.update = mock_update
        mock_using = Mock()
        mock_using.filter = Mock(return_value=mock_filter)
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects

        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class

        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            with patch('app_snowflake.repos.recounter_repo.get_now_timestamp_ms', return_value=new_timestamp):
                from app_snowflake.repos.recounter_repo import update_recounter
                result = update_recounter(origin, data_dict)

        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_using.filter.assert_called_once_with(id=origin.id)
        mock_update.assert_called_once_with(
            id=origin.id,
            dcid=origin.dcid,
            mid=origin.mid,
            rc=20,  # Updated value from data_dict
            ct=origin.ct,
            ut=new_timestamp,
        )
        self.assertEqual(result, 1)

    def test_update_recounter_without_recount(self):
        """Test update_recounter function without recount in data_dict"""
        new_timestamp = 9876543210000
        
        origin = Mock()
        origin.id = 1
        origin.dcid = self.datacenter_id
        origin.mid = self.machine_id
        origin.rc = 15
        origin.ct = self.timestamp

        data_dict = {}  # No recount key
        mock_update = Mock(return_value=1)  # update returns number of rows updated
        mock_filter = Mock()
        mock_filter.update = mock_update
        mock_using = Mock()
        mock_using.filter = Mock(return_value=mock_filter)
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects

        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class

        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            with patch('app_snowflake.repos.recounter_repo.get_now_timestamp_ms', return_value=new_timestamp):
                from app_snowflake.repos.recounter_repo import update_recounter
                result = update_recounter(origin, data_dict)

        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_using.filter.assert_called_once_with(id=origin.id)
        mock_update.assert_called_once_with(
            id=origin.id,
            dcid=origin.dcid,
            mid=origin.mid,
            rc=origin.rc,  # Should keep original value
            ct=origin.ct,
            ut=new_timestamp,
        )
        self.assertEqual(result, 1)

    def test_get_recounter(self):
        """Test get_recounter function"""
        mock_instance = Mock()
        mock_get = Mock(return_value=mock_instance)
        mock_using = Mock()
        mock_using.get = mock_get
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects

        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class

        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            from app_snowflake.repos.recounter_repo import get_recounter
            result = get_recounter(self.datacenter_id, self.machine_id)

        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_get.assert_called_once_with(
            dcid=self.datacenter_id,
            mid=self.machine_id,
        )
        self.assertEqual(result, mock_instance)

    def test_get_recounter_with_different_ids(self):
        """Test get_recounter with different datacenter and machine IDs"""
        mock_instance = Mock()
        mock_get = Mock(return_value=mock_instance)
        mock_using = Mock()
        mock_using.get = mock_get
        mock_objects = Mock()
        mock_objects.using = Mock(return_value=mock_using)
        mock_recounter_class = Mock()
        mock_recounter_class.objects = mock_objects
        test_dcid = 10
        test_mid = 1000

        mock_model_module = MagicMock()
        mock_model_module.Recounter = mock_recounter_class

        with patch.dict(sys.modules, {'app_snowflake.models.recounter': mock_model_module}):
            if 'app_snowflake.repos.recounter_repo' in sys.modules:
                del sys.modules['app_snowflake.repos.recounter_repo']
            
            from app_snowflake.repos.recounter_repo import get_recounter
            result = get_recounter(test_dcid, test_mid)

        mock_objects.using.assert_called_once_with('snowflake_rw')
        mock_get.assert_called_once_with(
            dcid=test_dcid,
            mid=test_mid,
        )
        self.assertEqual(result, mock_instance)
