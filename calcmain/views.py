from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse
from django.utils import timezone
from .forms import SheetUploadForm
from .models import StudyAnalysis


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
    # calculating 필요
    context = {"study": study}
    return render(request, "calcmain/data_confirm.html", context)
