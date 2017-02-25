from django import forms
from .models import StudyAnalysis


class SheetUploadForm(forms.ModelForm):

    class Meta:
        model = StudyAnalysis
        fields = ('study_name', 'treatment_name', 'imported_sheet', 'up_patients')
