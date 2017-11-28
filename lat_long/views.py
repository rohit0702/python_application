from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from lat_long.models import Document
from lat_long.forms import DocumentForm
import xlrd
from upload.settings import BASE_DIR
import requests
import xlwt, itertools
import datetime
from django.http import HttpResponse
import os
now = datetime.datetime.now()
from xlutils.copy import copy



def home(request):
    documents = Document.objects.all()
    return render(request, 'lat_long/home.html', { 'documents': documents })





def model_form_upload(request):
    col_width = 256 * 30                        # 30 characters wide
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        for filename, file in request.FILES.iteritems():
            file = request.FILES[filename].name
        print file,"adasdasd"
        doc = 'documents/'+str(file)
        is_doc = Document.objects.filter(document=doc)
        if is_doc:
            is_doc.delete()
        try:
            file_path_name = str(BASE_DIR)+'/'+'media'+'/'+'documents'+'/'+str(file)
            os.remove(file_path_name)
        except OSError:
            pass
        is_xlsx = file.split('.')[-1]
        if not is_xlsx in ['xlsx']:
            return HttpResponse('Invalid File. Please upload xlsx file.')
        if form.is_valid():
            form.save()
            final_result = []
            error_result = []
            file_name = str(BASE_DIR)+'/'+'media'+'/'+'documents'+'/'+str(file)
            wb = xlrd.open_workbook(file_name)
            sh = wb.sheet_by_index(0)
            write_book = copy(wb)
            sheet = write_book.get_sheet(0)
            address = [ str(x) for x in sh.col_values(0)[1:]]
            for add in address:
                try:
                    url_address = add.replace(' ','+')
                    url = 'http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false' % url_address
                    response = requests.get(url)
                    resp_json_payload = response.json()
                    val = resp_json_payload['results'][0]['geometry']['location']
                    final_result.append((add,val.get('lat'),val.get('lng')))
                except Exception as e:
                    error_result.append((add,'NA','NA'))
                    continue
            if error_result:
                final_result.extend(error_result)

            try:
                for i in itertools.count():
                    sheet.col(i).width = col_width
            except ValueError:
                pass
            eval_test = 'Python Evaluation Test'
            sid='Latitude & Longitude Report'
            sheet.write(0, 4, "Purpose : %s " % eval_test)
            sheet.write(2, 4, "DATA : %s " % sid)
            sheet.write(3, 4, "Date : %s " %now.strftime('%d-%m-%Y'))

            sheet.write(0, 1, "Latitude")
            sheet.write(0, 2, "Longitude")
            row=1
            for i in final_result:
                sheet.write(row, 0, str(i[0]))
                sheet.write(row, 1, str(i[1]))
                sheet.write(row, 2, str(i[2]))
                row = row+1
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=%s'% str(file)
            write_book.save(response)
            return response
    else:
        form = DocumentForm()
    return render(request, 'lat_long/model_form_upload.html', {
        'form': form
    })


