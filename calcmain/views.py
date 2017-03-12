from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import SheetUploadForm
from .models import StudyAnalysis, ProbExcelSheets
import re
import math
import pandas as pd
import numpy as np
from bokeh.charts import Bar, Histogram  # defaults, output_file, show
from bokeh.models import Range1d, Span, Label, BoxAnnotation
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
    process_df.loc[:, "Number of solid organ tumor"] = 0
    process_df.loc[:, "Number of lymph node"] = 0
    process_df.loc[:, "Tumor burden at the baseline (mm)"] = 0  # Sum of all lesion size at baseline per patient(ID)
    process_df.loc[:, "Tumor burden at the post-treatment (mm)"] = 0 # Sum of all lesion size at post-treatment per patient(ID)
    process_df.loc[:, "Lesion size at the baseline (mm)"] = np.nan # For checking patients who have only one lesion (Solid or Lymph)
    process_df.loc[:, "Percent change (%)"] = 0

    # Check records and update cells
    for record in range(len(main_df.index)):
        record_id = main_df.iloc[:, 0][record]
        lesion_name = main_df.iloc[:, 1][record]
        input_id = record_id - 1

        if re.match("lymph*", lesion_name):
            process_df.loc[input_id, "Number of lymph node"] += 1
        else:
            process_df.loc[input_id, "Number of solid organ tumor"] += 1
        process_df.loc[input_id, "Tumor burden at the baseline (mm)"] += main_df.iloc[:, 2][record]
        process_df.loc[input_id, "Tumor burden at the post-treatment (mm)"] += main_df.iloc[:, 3][record]


    process_df.loc[:, "Number of solid organ tumor"] = process_df.loc[:, "Number of solid organ tumor"].astype(int)
    process_df.loc[:, "Number of lymph node"] = process_df.loc[:, "Number of lymph node"].astype(int)
    process_df.loc[:, "Tumor burden at the baseline (mm)"] = process_df.loc[:, "Tumor burden at the baseline (mm)"].astype(int)
    process_df.loc[:, "Tumor burden at the post-treatment (mm)"] = process_df.loc[:, "Tumor burden at the post-treatment (mm)"].astype(int)

    # Check processed dataframe and update cells
    for record in range(len(process_df.index)):
        process_df.loc[record, 'Percent change (%)'] = math.floor((process_df.loc[record, "Tumor burden at the post-treatment (mm)"] - process_df.loc[record, "Tumor burden at the baseline (mm)"]) / process_df.loc[record, "Tumor burden at the baseline (mm)"] * 100)
        if process_df.loc[record, "Number of lymph node"] + process_df.loc[record, "Number of solid organ tumor"] == 1:
            process_df.loc[record, "Lesion size at the baseline (mm)"] = int(main_df.loc[main_df['ID'] == record + 1]['Lesion size at baseline (mm)'])

    study.processed_df = process_df
    study.save()

    context = {
        "study": study,
        "data": process_df.to_html(
            columns=['Patient ID', 'Number of solid organ tumor', 'Number of lymph node', 'Percent change (%)', 'Tumor burden at the baseline (mm)', 'Tumor burden at the post-treatment (mm)'],
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
        if processed_df.loc[:, "Percent change (%)"][id] <= -30:
            num_partial_response += 1
        elif processed_df.loc[:, "Percent change (%)"][id] >= 20:
            num_progression += 1

    partial_response_prop = round(num_partial_response / num_all_patients * 100, 2)
    progression_prop = round((num_progression + up_patients) / num_all_patients * 100, 2)

    # Draw a plot for visualizing patients' diagnosis results.
    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Percent change (%)': sorted(processed_df.loc[:, "Percent change (%)"], reverse=True)}
    sorted_df = pd.DataFrame(new_data)

    study.sorted_df = sorted_df
    study.save()

    sorted_plot = Bar(sorted_df, values='Percent change (%)', color="White", title='Percent change (%)', legend=None, ylabel="", ygrid=False)
    sorted_plot.y_range = Range1d(-100, 100)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600

    line_pr = Span(location=-30, dimension='width', line_color='blue', line_alpha=0.4, line_dash='solid', line_width=2,)
    line_pro = Span(location=20, dimension='width', line_color='red', line_alpha=0.4, line_dash='solid', line_width=2,)
    sorted_plot.add_layout(line_pr)
    sorted_plot.add_layout(line_pro)

    # line-only : x=400, y=135
    citation_pr = Label(x=250, y=170, x_units='screen', y_units='screen',
                     text='Progression (+20%)', text_color='red', text_alpha=0.4, render_mode='css',)
    # line-only : x=375, y=80
    citation_pro = Label(x=235, y=30, x_units='screen', y_units='screen',
                     text='Partial response (-30%)', text_color='blue', text_alpha=0.4, render_mode='css',)
    sorted_plot.add_layout(citation_pr)
    sorted_plot.add_layout(citation_pro)

    pr_box = BoxAnnotation(top=-30, fill_alpha=0.1, fill_color='blue')
    pro_box = BoxAnnotation(bottom=20, fill_alpha=0.1, fill_color='red')
    sorted_plot.add_layout(pr_box)
    sorted_plot.add_layout(pro_box)

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


# Calculate the intra-observer measurement error
def data_reassessment1(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)

    # 1-1) Load probability excel files
    Intra_PR_Multiple = get_object_or_404(ProbExcelSheets, sheets_name="Intra_PR_Multiple")
    Intra_PR_Singular = get_object_or_404(ProbExcelSheets, sheets_name="Intra_PR_Singular")
    Intra_Pro_Multiple = get_object_or_404(ProbExcelSheets, sheets_name="Intra_Pro_Multiple")
    Intra_Pro_Singular = get_object_or_404(ProbExcelSheets, sheets_name="Intra_Pro_Singular")
    PR_Multiple = pd.read_excel(Intra_PR_Multiple.imported_sheet, sheetname=0)
    PR_Singular = pd.read_excel(Intra_PR_Singular.imported_sheet, sheetname=0)
    Pro_Multiple = pd.read_excel(Intra_Pro_Multiple.imported_sheet, sheetname=0)
    Pro_Singular = pd.read_excel(Intra_Pro_Singular.imported_sheet, sheetname=0)

    # 1-2) Change the index of probability dataframe
    def change_index(pd_input):
        pd_input.loc[:, 'PercentChange'] = np.round(pd_input.loc[:, 'PercentChange'])
        pd_input.loc[:, 'PercentChange'] = pd_input.loc[:, 'PercentChange'].astype(int)
        pd_input = pd_input.set_index(['PercentChange'])
        pd_input.columns = pd_input.columns.astype(str)
        return pd_input
    PR_Multiple = change_index(PR_Multiple)
    PR_Singular = change_index(PR_Singular)
    Pro_Multiple = change_index(Pro_Multiple)
    Pro_Singular = change_index(Pro_Singular)

    # 2-1) Prepare the new dataframe about reassessment result (PartialResponse, Progression)
    processed_df = study.processed_df[['Patient ID', 'Number of solid organ tumor', 'Number of lymph node', 'Lesion size at the baseline (mm)', 'Percent change (%)']]
    processed_df.columns = ['ID', 'NS', 'NL', 'LS', 'PC']

    processed_df.loc[:, 'NS'] = processed_df.loc[:, 'NS'].astype(str)
    processed_df.loc[:, 'NL'] = processed_df.loc[:, 'NL'].astype(str)
    processed_df.loc[:, 'LS'] = processed_df.loc[:, 'LS'].astype(str)

    # 2-2) Setting the serial number to each record
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'LS'] != 'nan':
            processed_df.loc[record, 'old_status'] = processed_df.loc[record, 'NS'] + processed_df.loc[record, 'NL'] + str(int(float(processed_df.loc[record, 'LS'])))
        else:
            processed_df.loc[record, 'old_status'] = processed_df.loc[record, 'NS'] + processed_df.loc[record, 'NL']

    # 2-3) Making [percent change] exceeding 100 to 100
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'PC'] > 100:
            processed_df.loc[record, 'PC'] = 100

    # 2-4) Delete [# of Solid tumor & Lymph node] columns and make new columns
    processed_df = processed_df.drop(processed_df.columns[[1, 2]], axis=1)
    processed_df.loc[:, 'new_PR'] = processed_df.loc[:, 'new_PRO'] = 0

    # 3) Match the records' serial numbers to the probability-df's data
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'LS'] == 'nan':  # multiple
            processed_df.loc[record, 'new_PR'] = PR_Multiple.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
            processed_df.loc[record, 'new_PRO'] = Pro_Multiple.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
        else:  # singular
            processed_df.loc[record, 'new_PR'] = PR_Singular.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
            processed_df.loc[record, 'new_PRO'] = Pro_Singular.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]

    # 4) Save the new dataframe
    study.reassessed_df = processed_df
    study.save()

    # 5) Draw a plot for visualizing patients' diagnosis results.
    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Probability of PR (%)': sorted(processed_df.loc[:, "new_PR"], reverse=False)}
    sorted_df = pd.DataFrame(new_data)
    sorted_plot = Bar(sorted_df, values='Probability of PR (%)', color="Blue", title='', legend=None, ylabel="")
    sorted_plot.y_range = Range1d(0, 1)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600
    script_PR, div_PR = components(sorted_plot)

    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Probability of Pro (%)': sorted(processed_df.loc[:, "new_PRO"], reverse=True)}
    sorted_df = pd.DataFrame(new_data)
    sorted_plot = Bar(sorted_df, values='Probability of Pro (%)', color="Red", title='', legend=None, ylabel="")
    sorted_plot.y_range = Range1d(0, 1)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600
    script_Pro, div_Pro = components(sorted_plot)

    # Summarized data (initial waterfall plot)
    sorted_df = study.sorted_df
    sorted_plot = Bar(sorted_df, values='Percent change (%)', color="White", title='Percent change (%)', legend=None, ylabel="", ygrid=False)
    sorted_plot.y_range = Range1d(-100, 100)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600

    line_pr = Span(location=-30, dimension='width', line_color='blue', line_alpha=0.4, line_dash='solid', line_width=2,)
    line_pro = Span(location=20, dimension='width', line_color='red', line_alpha=0.4, line_dash='solid', line_width=2,)
    sorted_plot.add_layout(line_pr)
    sorted_plot.add_layout(line_pro)

    # line-only : x=400, y=135
    citation_pr = Label(x=250, y=170, x_units='screen', y_units='screen',
                     text='Progression (+20%)', text_color='red', text_alpha=0.4, render_mode='css',)
    # line-only : x=375, y=80
    citation_pro = Label(x=235, y=30, x_units='screen', y_units='screen',
                     text='Partial response (-30%)', text_color='blue', text_alpha=0.4, render_mode='css',)
    sorted_plot.add_layout(citation_pr)
    sorted_plot.add_layout(citation_pro)

    pr_box = BoxAnnotation(top=-30, fill_alpha=0.1, fill_color='blue')
    pro_box = BoxAnnotation(bottom=20, fill_alpha=0.1, fill_color='red')
    sorted_plot.add_layout(pr_box)
    sorted_plot.add_layout(pro_box)

    script_summary, div_summary = components(sorted_plot)

    assumption_num = "1"
    radiologist = "Same"

    up_patients = study.up_patients

    context = {
        "study": study,
        "assumption_num": assumption_num,
        "radiologist": radiologist,
        "script_summary": script_summary,
        "div_summary": div_summary,
        "script_PR": script_PR,
        "div_PR": div_PR,
        "script_Pro": script_Pro,
        "div_Pro": div_Pro,
        "up_patients": up_patients
    }
    return render(request, "calcmain/reassessment_result.html", context)


# Calculate the inter-observer measurement error
def data_reassessment2(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)

    Inter_PR_Multiple = get_object_or_404(ProbExcelSheets, sheets_name="Inter_PR_Multiple")
    Inter_PR_Singular = get_object_or_404(ProbExcelSheets, sheets_name="Inter_PR_Singular")
    Inter_Pro_Multiple = get_object_or_404(ProbExcelSheets, sheets_name="Inter_Pro_Multiple")
    Inter_Pro_Singular = get_object_or_404(ProbExcelSheets, sheets_name="Inter_Pro_Singular")
    PR_Multiple = pd.read_excel(Inter_PR_Multiple.imported_sheet, sheetname=0)
    PR_Singular = pd.read_excel(Inter_PR_Singular.imported_sheet, sheetname=0)
    Pro_Multiple = pd.read_excel(Inter_Pro_Multiple.imported_sheet, sheetname=0)
    Pro_Singular = pd.read_excel(Inter_Pro_Singular.imported_sheet, sheetname=0)

    # 1-2) Change the index of probability dataframe
    def change_index(pd_input):
        pd_input.loc[:, 'PercentChange'] = np.round(pd_input.loc[:, 'PercentChange'])
        pd_input.loc[:, 'PercentChange'] = pd_input.loc[:, 'PercentChange'].astype(int)
        pd_input = pd_input.set_index(['PercentChange'])
        pd_input.columns = pd_input.columns.astype(str)
        return pd_input
    PR_Multiple = change_index(PR_Multiple)
    PR_Singular = change_index(PR_Singular)
    Pro_Multiple = change_index(Pro_Multiple)
    Pro_Singular = change_index(Pro_Singular)

    # 2-1) Prepare the new dataframe about reassessment result (PartialResponse, Progression)
    processed_df = study.processed_df[['Patient ID', 'Number of solid organ tumor', 'Number of lymph node', 'Lesion size at the baseline (mm)', 'Percent change (%)']]
    processed_df.columns = ['ID', 'NS', 'NL', 'LS', 'PC']

    processed_df.loc[:, 'NS'] = processed_df.loc[:, 'NS'].astype(str)
    processed_df.loc[:, 'NL'] = processed_df.loc[:, 'NL'].astype(str)
    processed_df.loc[:, 'LS'] = processed_df.loc[:, 'LS'].astype(str)

    # 2-2) Setting the serial number to each record
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'LS'] != 'nan':
            processed_df.loc[record, 'old_status'] = processed_df.loc[record, 'NS'] + processed_df.loc[record, 'NL'] + str(int(float(processed_df.loc[record, 'LS'])))
        else:
            processed_df.loc[record, 'old_status'] = processed_df.loc[record, 'NS'] + processed_df.loc[record, 'NL']

    # 2-3) Making [percent change] exceeding 100 to 100
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'PC'] > 100:
            processed_df.loc[record, 'PC'] = 100

    # 2-4) Delete [# of Solid tumor & Lymph node] columns and make new columns
    processed_df = processed_df.drop(processed_df.columns[[1, 2]], axis=1)
    processed_df.loc[:, 'new_PR'] = processed_df.loc[:, 'new_PRO'] = 0

    # 3) Match the records' serial numbers to the probability-df's data
    for record in range(len(processed_df.index)):
        if processed_df.loc[record, 'LS'] == 'nan':  # multiple
            processed_df.loc[record, 'new_PR'] = PR_Multiple.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
            processed_df.loc[record, 'new_PRO'] = Pro_Multiple.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
        else:  # singular
            processed_df.loc[record, 'new_PR'] = PR_Singular.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]
            processed_df.loc[record, 'new_PRO'] = Pro_Singular.loc[processed_df.loc[record, 'PC'], processed_df.loc[record, 'old_status']]

    # 4) Save the new dataframe
    study.reassessed_df = processed_df
    study.save()

    # 5) Draw a plot for visualizing patients' diagnosis results.
    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Probability of PR (%)': sorted(processed_df.loc[:, "new_PR"], reverse=False)}
    sorted_df = pd.DataFrame(new_data)
    sorted_plot = Bar(sorted_df, values='Probability of PR (%)', color="Blue", title='', legend=None, ylabel="")
    sorted_plot.y_range = Range1d(0, 1)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600
    script_PR, div_PR = components(sorted_plot)

    new_data = {'Index': [i + 1 for i in range(len(processed_df.index))],
               'Probability of Pro (%)': sorted(processed_df.loc[:, "new_PRO"], reverse=True)}
    sorted_df = pd.DataFrame(new_data)
    sorted_plot = Bar(sorted_df, values='Probability of Pro (%)', color="Red", title='', legend=None, ylabel="")
    sorted_plot.y_range = Range1d(0, 1)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600
    script_Pro, div_Pro = components(sorted_plot)

    # Summarized data (initial waterfall plot)
    sorted_df = study.sorted_df
    sorted_plot = Bar(sorted_df, values='Percent change (%)', color="White", title='Percent change (%)', legend=None, ylabel="", ygrid=False)
    sorted_plot.y_range = Range1d(-100, 100)
    sorted_plot.xaxis.visible = False
    sorted_plot.title.text_font = "Roboto Slab"
    sorted_plot.background_fill_alpha = 0
    sorted_plot.border_fill_color = None
    sorted_plot.width = 600    # default : 600
    sorted_plot.height = 250    # default : 600

    line_pr = Span(location=-30, dimension='width', line_color='blue', line_alpha=0.4, line_dash='solid', line_width=2,)
    line_pro = Span(location=20, dimension='width', line_color='red', line_alpha=0.4, line_dash='solid', line_width=2,)
    sorted_plot.add_layout(line_pr)
    sorted_plot.add_layout(line_pro)

    # line-only : x=400, y=135
    citation_pr = Label(x=250, y=170, x_units='screen', y_units='screen',
                     text='Progression (+20%)', text_color='red', text_alpha=0.4, render_mode='css',)
    # line-only : x=375, y=80
    citation_pro = Label(x=235, y=30, x_units='screen', y_units='screen',
                     text='Partial response (-30%)', text_color='blue', text_alpha=0.4, render_mode='css',)
    sorted_plot.add_layout(citation_pr)
    sorted_plot.add_layout(citation_pro)

    pr_box = BoxAnnotation(top=-30, fill_alpha=0.1, fill_color='blue')
    pro_box = BoxAnnotation(bottom=20, fill_alpha=0.1, fill_color='red')
    sorted_plot.add_layout(pr_box)
    sorted_plot.add_layout(pro_box)

    script_summary, div_summary = components(sorted_plot)

    assumption_num = "2"
    radiologist = "Another"

    up_patients = study.up_patients

    context = {
        "study": study,
        "assumption_num": assumption_num,
        "radiologist": radiologist,
        "script_summary": script_summary,
        "div_summary": div_summary,
        "script_PR": script_PR,
        "div_PR": div_PR,
        "script_Pro": script_Pro,
        "div_Pro": div_Pro,
        "up_patients": up_patients
    }
    return render(request, "calcmain/reassessment_result.html", context)


def final_result(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    input_df = study.reassessed_df

    # 1) Add rows of UP patients.
    base_index = len(input_df.index)
    for i in range(study.up_patients):
        input_df.loc[base_index + i, "new_PR"] = 0
        input_df.loc[base_index + i, "new_PRO"] = 1

    # 2) Generate 1000 sets of new variables(1or0) following bernoulli distribution.
    # Key = Patient ID, Value = Bernoulli random variable
    bernoulli_dict_PR = {}
    bernoulli_dict_PR0 = {}
    # Column = Key = Patients' ID, Row = Value = 1000 Bernoulli random variables derived from patients new_PR or new_PRO proportion
    for record in range(len(input_df.index)):
        bernoulli_dict_PR[record] = np.random.choice([0, 1], size=(1000,), p=[1-input_df.loc[record, 'new_PR'], input_df.loc[record, 'new_PR']])
        bernoulli_dict_PR0[record] = np.random.choice([0, 1], size=(1000,), p=[1-input_df.loc[record, 'new_PRO'], input_df.loc[record, 'new_PRO']])
        # bernoulli_dict_PR[record] = bernoulli.rvs(input_df.loc[record, 'new_PR'], size=1000)
        # bernoulli_dict_PR0[record] = bernoulli.rvs(input_df.loc[record, 'new_PRO'], size=1000)

    # 3) Make dataframes of variables and calculate each trials' (rows') means.
    PR_df = pd.DataFrame(bernoulli_dict_PR)
    PR_df.loc[:, "NewProb(PR)"] = PR_df.sum(axis=1) / len(PR_df.columns)
    PRO_df = pd.DataFrame(bernoulli_dict_PR0)
    PRO_df.loc[:, "NewProb(PRO)"] = PRO_df.sum(axis=1) / len(PRO_df.columns)

    # 4) Make new dataframes with calculated means and find quantile numbers
    new_data = {'Index': [i + 1 for i in range(len(PR_df.index))],
               'Probability of PR (%)': sorted((PR_df.loc[:, "NewProb(PR)"] * 100).astype(int), reverse=False)}
    sorted_PR_df = pd.DataFrame(new_data)

    quantile_bottom_pr = sorted_PR_df.loc[25, "Probability of PR (%)"] # 26th
    quantile_top_pr = sorted_PR_df.loc[974, "Probability of PR (%)"] # 975th
    quantile_median_pr = int((sorted_PR_df.loc[499, "Probability of PR (%)"] + sorted_PR_df.loc[500, "Probability of PR (%)"]) / 2)

    new_data = {'Index': [i + 1 for i in range(len(PRO_df.index))],
               'Probability of PRO (%)': sorted((PRO_df.loc[:, "NewProb(PRO)"] * 100).astype(int), reverse=False)}
    sorted_PRO_df = pd.DataFrame(new_data)

    quantile_bottom_pro = sorted_PRO_df.loc[25, "Probability of PRO (%)"] # 26th
    quantile_top_pro = sorted_PRO_df.loc[974, "Probability of PRO (%)"] # 975th
    quantile_median_pro = int((sorted_PRO_df.loc[499, "Probability of PRO (%)"] + sorted_PRO_df.loc[500, "Probability of PRO (%)"]) / 2)

    # 5) Draw histogram plots for visualizing calculation results.
    # pr_plot = Histogram(sorted_PR_df, values='Probability of PR (%)', bins=7, color='blue', title='', ylabel='', xlabel='') # 15
    pr_plot = Bar(sorted_PR_df, label='Probability of PR (%)', bar_width=1, values="Index", agg="count", color='blue', title='', ylabel='', xlabel='', legend=False)
    pr_plot.title.text_font = "Roboto Slab"
    pr_plot.background_fill_alpha = 0
    pr_plot.border_fill_color = None
    # pr_plot.x_range = Range1d(quantile_bottom_pr-20, quantile_top_pr+20)
    pr_plot.width = 600    # default : 600
    pr_plot.height = 600    # default : 600
    script_PR, div_PR = components(pr_plot)

    # pro_plot = Histogram(sorted_PRO_df, values='Probability of PRO (%)', bins=7, color='red', title='', ylabel='', xlabel='') # 15
    pro_plot = Bar(sorted_PRO_df, label='Probability of PRO (%)', bar_width=1, values="Index", agg="count", color='red', title='', ylabel='', xlabel='', legend=False)
    pro_plot.title.text_font = "Roboto Slab"
    pro_plot.background_fill_alpha = 0
    pro_plot.border_fill_color = None
    # pro_plot.x_range = Range1d(quantile_bottom_pro-20, quantile_top_pro+20)
    pro_plot.width = 600    # default : 600
    pro_plot.height = 600    # default : 600
    script_Pro, div_Pro = components(pro_plot)

    context = {
        "study": study,
        "quantile_bottom_pr": quantile_bottom_pr,
        "quantile_top_pr": quantile_top_pr,
        "quantile_median_pr": quantile_median_pr,
        "quantile_bottom_pro": quantile_bottom_pro,
        "quantile_top_pro": quantile_top_pro,
        "quantile_median_pro": quantile_median_pro,
        "script_PR": script_PR,
        "div_PR": div_PR,
        "script_Pro": script_Pro,
        "div_Pro": div_Pro
    }
    return render(request, "calcmain/final_result.html", context)


def export_delete(request, pk):
    study = get_object_or_404(StudyAnalysis, pk=pk)
    study.imported_sheet.delete()
    study.delete()

    return render(request, "calcmain/deleted.html", {})
