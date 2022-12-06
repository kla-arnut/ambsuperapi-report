from django.shortcuts import render
from django.http import HttpResponse
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
    return render(request, "input.html")
    #return HttpResponse("Hello, world. You're at the user report index.")

@csrf_exempt
def getreport(request):
    secretKey = request.POST['secret_key']
    loginUser = request.POST['login_user']
    loginPassword = request.POST['login_password']
    agentUser = request.POST['agent_user']
    memberUser = request.POST['member_user']

    # check key
    if userReportObj.checkSecretKey(secretKey) == False:
        return HttpResponse(json.dumps({'success':False,'message':'secret key error','data':{}}))

    # worker
    dataRes = userReportObj.worker(loginUser,loginPassword,agentUser,memberUser)