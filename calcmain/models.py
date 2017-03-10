from django.db import models
from django.utils import timezone
from picklefield.fields import PickledObjectField


class StudyAnalysis(models.Model):
    study_name = models.CharField(max_length=200)
    treatment_name = models.CharField(max_length=200)
    imported_sheet = models.FileField(upload_to='files/imported_sheets')
    up_patients = models.IntegerField()
    processed_df = PickledObjectField(default="None")
    sorted_df = PickledObjectField(default="None")
    reassessed_df = PickledObjectField(default="None")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.study_name


class ProbExcelSheets(models.Model):
    sheets_name = models.CharField(max_length=200)
    imported_sheet = models.FileField(upload_to='files/prob_excel_sheets')

    def __str__(self):
        return self.sheets_name
