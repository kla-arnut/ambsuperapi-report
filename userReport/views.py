from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

try:
    import configs
except ImportError:
    configs = {}
try:
    from userReport.userReport import userReport
    userReportObj = userReport()
except :
    print ("Object Error")
    exit()


def index(request):
    return render(request, "input.html")
    #return HttpResponse("Hello, world. You're at the user report index.")

@csrf_exempt
def getreport(request):
    secretKey = request.POST['secret_key']
    agentUser = request.POST['agent_user']
    agentPassword = request.POST['agent_password']
    customerUser = request.POST['customer_user']

    if userReportObj.checkSecretKey(secretKey) == False:
        return HttpResponse(json.dumps({'success':False,'message':'secret key error','data':{}}))

    # login
    userReportObj.getpage()

    # crawler page report/winLose by agent name

    # crawler page report/winLose?id={USERID}&currency=THB