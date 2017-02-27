from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse
from django.utils import timezone
from .forms import SheetUploadForm
from .models import StudyAnalysis
import re
import math
import pandas as pd
import numpy as np
from bokeh.charts import Bar, defaults  # output_file, show
from bokeh.models import Range1d
from bokeh.embed import components


def mainpage(request):
    return render(request, "calcmain/mainpage.html", {})


def introduction(request):
    return render(request, "calcmain/introduction.html", {})


def dataimport(request):
    if request.method == "POST":
        form = SheetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            study = form.save(commit=False)
            study.createdAt = timezone.now()
            study.save()
            return redirect('calcmain:data_confirm', pk=study.pk)
    else:
        form = SheetUploadForm()
    context = {'form': form}
    return render(request, "calcmain/dataimport.html", context)


def data_confirm(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    up_patients = study.up_patients
    main_df = pd.read_excel(study.imported_sheet, sheetname=0)
    num_patients_imported = len(main_df.ID.unique())
    num_all_patients = num_patients_imported + up_patients

    context = {
        "study": study,
        "num_patients_imported": num_patients_imported,
        "num_all_patients": num_all_patients
    }
    return render(request, "calcmain/data_confirm.html", context)


def data_process(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    main_df = pd.read_excel(study.imported_sheet, sheetname=0)

    # Change column names and change uppercase characters(organ) into lowercase
    main_df.columns = ['ID', 'Organ', 'Lesion size at baseline (mm)', 'Lesion size at post-treatment (mm)']
    main_df["Organ"] = main_df["Organ"].str.lower()

    # Generate a dataframe for processing the data
    process_df = pd.DataFrame({'Patient ID': list(set([int(i) for i in main_df.ID]))})
    process_df["Number of solid tumor"] = 0
    process_df["Number of lymph node"] = 0
    process_df["sum_base"] = 0
    process_df["sum_post"] = 0
    process_df["Lesion size at the baseline (mm)"] = np.nan
    process_df["Percent change (%)"] = 0

    # Check records and update cells
    for record in range(len(main_df.index)):
        record_id = main_df.iloc[:, 0][record]
        lesion_name = main_df.iloc[:, 1][record]
        input_id = record_id - 1

        if re.match("lymph*", lesion_name):
            process_df["Number of lymph node"][input_id] += 1
        else:
            process_df["Number of solid tumor"][input_id] += 1
        process_df["sum_base"][input_id] += main_df.iloc[:, 2][record]
        process_df["sum_post"][input_id] += main_df.iloc[:, 3][record]

    # Check processed dataframe and update cells
    for record in range(len(process_df.index)):
        process_df['Percent change (%)'][record] = math.floor((process_df["sum_post"][record] - process_df["sum_base"][record]) / process_df["sum_base"][record] * 100)
        if process_df["Number of lymph node"][record] + process_df["Number of solid tumor"][record] == 1:
            process_df["Lesion size at the baseline (mm)"][record] = int(main_df.loc[main_df['ID'] == record + 1]['Lesion size at baseline (mm)'])

    study.processed_df = process_df
    study.save()

    context = {
        "study": study,
        "data": process_df.to_html(
            columns=['Patient ID', 'Number of solid tumor', 'Number of lymph node', 'Percent change (%)', 'Lesion size at the baseline (mm)'],
            index=False, na_rep="", bold_rows=True, classes=["table", "table-hover", "table-processed"])
    }
    return render(request, "calcmain/data_processed.html", context)


def data_summary(request, pk):

    study = get_object_or_404(StudyAnalysis, pk=pk)
    processed_df = study.processed_df
    up_patients = study.up_patients
    num_all_patients = len(processed_df.index) + up_patients

    # Calculate the proportions of patients based on diagnosis results.
    num_partial_response = num_progression = 0
    for id in range(len(processed_df.index)):
        if processed_df.loc[:, "Percent change (%)"][id] < -30:
            num_partial_response += 1
        elif processed_df.loc[:, "Percent change (%)"][id] >= 20:
            num_progression += 1

    partial_response_prop = round(num_partial_response / num_all_patients * 100, 2)
    progression_prop = round((num_progression + up_patients) / num_all_patients * 100, 2)

    # Draw a plot for visualizing patients' diagnosis results.
    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Percent change (%)': sorted(processed_df.loc[:, "Percent change (%)"], reverse=True)}
    sorted_df = pd.DataFrame(new_data)

    sorted_plot = Bar(sorted_df, values='Percent change (%)', color="Blue", title='Percent change (%)', legend=None, ylabel="")
    sorted_plot.y_range = Range1d(-100, 100)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600

    script, div = components(sorted_plot)

    context = {
        "study": study,
        "num_all_patients": num_all_patients,
        "partial_response_prop": partial_response_prop,
        "progression_prop": progression_prop,
        "script": script,
        "div": div
    }
    return render(request, "calcmain/data_summary.html", context)


def data_reassessment1(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    print("assess 1")
    context = {
        "study": study
    }
    return render(request, "calcmain/reassessment_result.html", context)


def data_reassessment2(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    print("assess 2")
    context = {
        "study": study
    }
    return render(request, "calcmain/reassessment_result.html", context)


def final_result(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    print("Final result")
    context = {
        "study": study
    }
    return render(request, "calcmain/final_result.html", context)


def export_delete(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    print("Export_delete")
    context = {
        "study": study
    }
    return render(request, "calcmain/deleted.html", context)
