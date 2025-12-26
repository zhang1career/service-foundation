from django import forms


class UploadingFileForm(forms.Form):
    """
    Form for uploading text files
    """
    file = forms.FileField(label='Select a text file')
