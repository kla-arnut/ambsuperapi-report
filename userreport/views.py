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

    secretKey = agentUser = memberUser = dateStart = dateEnd = ''
    # param checker
    if request.method == 'POST':
        secretKey = request.POST.get('secret_key')
        agentUser = request.POST.get('agent_user')
        memberUser = request.POST.get('member_user')
        dateStart = request.POST.get('date_start')
        dateEnd = request.POST.get('date_end')
    elif request.method == 'GET':
        secretKey = request.GET.get('secret_key')
        agentUser = request.GET.get('agent_user')
        memberUser = request.GET.get('member_user')
        dateStart = request.GET.get('date_start')
        dateEnd = request.GET.get('date_end')

    #check param
    if secretKey == None or agentUser == None or memberUser == None or dateStart == None or dateEnd == None:
        return JsonResponse({'success':False,'message':'corrupt parameter','data':{}})

    # check key
    checkSecret = userReportObj.checkSecretKey(secretKey)
    if checkSecret['success'] == False:
        return JsonResponse(checkSecret)

    # worker
    dataRes = userReportObj.getReport(agentUser,memberUser,dateStart,dateEnd)

    return JsonResponse(dataRes)