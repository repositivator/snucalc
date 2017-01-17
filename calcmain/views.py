from django.shortcuts import render
# from . import models

def mainpage(request):
    return render(request,"calcmain/mainpage.html",{})
