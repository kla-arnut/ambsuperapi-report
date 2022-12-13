from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

try:
    import configs
except ImportError:
    configs = {}
try:
    from userreport.userReport import userReport
    userReportObj = userReport()
except :
    print ("Object Error")
    exit()


def index(request):
    allToken = userReportObj.getAllToken()
    return render(request, "input.html", {'allToken':allToken.items()})
    #return HttpResponse("Hello, world. You're at the user report index.")

@csrf_exempt
def getreport(request):
    secretKey = request.POST['secret_key']
    agentUser = request.POST['agent_user']
    memberUser = request.POST['member_user']
    dateStart = request.POST['date_start']
    dateEnd = request.POST['date_end']

    # check key
    checkSecret = userReportObj.checkSecretKey(secretKey)
    if checkSecret['success'] == False:
        return JsonResponse(checkSecret)

    # worker
    dataRes = userReportObj.getReport(agentUser,memberUser,dateStart,dateEnd)

    return JsonResponse(dataRes)