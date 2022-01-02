from django.shortcuts import render
from django.http import HttpResponse
import spacy
import openpyxl
from .models import Festival,Features
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Count
from django.views.decorators.csrf import csrf_protect 

list_of_monthes = [
    'january',
    'march',
    'may',
    'july',
    'september',
    'november',
    'february',
    'april',
    'june',
    'august',
    'october',
    'december' 
]

list_of_short_monthes = [
    'jan',
    'mar',
    'may',
    'jul',
    'sep',
    'nov',
    'feb',
    'apr',
    'jun',
    'aug',
    'oct',
    'dec' 
]

blacklist_words = [
    'and',
    'or'
]

def index(request):
    return render(request, 'search/index.html')
    

@csrf_protect
def search(request):
    view_data = {}
    if request.method == "POST":
        main_string = request.POST.get('string')

        # clean input string from non alpha-numeric characters
        clean_string = filter(lambda x: x.isalnum() or x.isspace(), main_string)
        clean_string = "".join(clean_string)

        print(clean_string)

        strings = clean_string.split('and')

        print(strings)

        inter_statements_query = Q()
        keywords = ""
        list_of_types = []

        for string in strings:

            types = []
            locs,dates,titles = extract_locations_and_dates(string)
            
            date_prim = month_search(string)
            for month in date_prim:
                if month not in dates:
                    dates.append(month)
            
            caches = get_features(string)
            for cache in caches:
                if cache.word not in blacklist_words:
                    if cache.type == 'title':
                        if cache.word not in titles:
                            titles.append(cache.word)
                    if cache.type == 'address':
                        if cache.word not in locs:
                            locs.append(cache.word)
                    if cache.type == 'date':
                        if cache.word not in dates:
                            dates.append(cache.word)
                    if cache.type == 'type':
                        if cache.word not in types:
                            types.append(cache.word)


            loc_query = Q()
            for loc in locs:
                loc_query = loc_query & Q(address__icontains=loc)
            if len(locs) != 0:
                keywords = keywords + " , " + ' , '.join(locs)

            date_query = Q()
            for date in dates:
                date_query = date_query & Q(date__icontains=date)
            if len(dates) != 0:
                keywords = keywords + " , " + ' , '.join(dates)

            title_query = Q()
            for title in titles:
                title_query = title_query & (Q(title__icontains=title) | Q(type__icontains=title))
            if len(titles) != 0:
                keywords = keywords + " , " + ' , '.join(titles)
            
            type_query = Q()
            for type in types:
                type_query = type_query & (Q(type__icontains=type) | Q(title__icontains=type))
            if len(types) != 0:
                keywords = keywords + " , " + ' , '.join(types)

            final_query = loc_query & date_query & title_query & type_query

            find_all_types = Festival.objects.filter(final_query).annotate(total_count=Count('id'))
            
            for special_type in find_all_types:
                if special_type.type not in list_of_types:
                    list_of_types.append(special_type.type)

            inter_statements_query = inter_statements_query | final_query

        
        print(inter_statements_query)

        view_data['all_results'] = Festival.objects.filter(inter_statements_query)
        view_data['string'] = main_string
        view_data['keywords'] = keywords[3:]
        view_data['types'] = list_of_types

    return render(request, 'search/result.html', view_data)


def extract_locations_and_dates(string):
    nlp_wk = spacy.load('en_core_web_sm')
    doc = nlp_wk(string)
    locations = []
    dates = []
    title = []
    for chunk in doc.ents:
        if chunk.label_ in ['LOC','GPE']:
            locations.append(chunk.text)
        elif chunk.label_ == 'DATE':
            dates.append(chunk.text)
        else:
            title.append(chunk.text)

    return locations,dates,title


def get_features(string):
    words = string.split()
    cached_features = []
    for word in words:
        if len(word) > 2 :
            cache = Features.objects.filter(word__istartswith=word).first()
            if cache :
                cached_features.append(cache)

    return cached_features


def upload_excel_to_db():
    Festival.objects.all().delete()
    
    excel_path = "static/data.xlsx"
    wb_obj = openpyxl.load_workbook(excel_path)
    sheet_obj = wb_obj.active
    row_num = sheet_obj.max_row

    for i in range(2,row_num):
        if sheet_obj.cell(row = i, column = 1).value:
            Festival(
                title = sheet_obj.cell(row = i, column = 1).value,
                date = sheet_obj.cell(row = i, column = 2).value,
                address = sheet_obj.cell(row = i, column = 3).value,
                lat = sheet_obj.cell(row = i, column = 4).value,
                long = sheet_obj.cell(row = i, column = 5).value,
                link = sheet_obj.cell(row = i, column = 6).value,
                type = sheet_obj.cell(row = i, column = 7).value
                ).save()


def extract_features_from_data():
    all_data = Festival.objects.all()
    already_added_title = []
    already_added_address = []
    already_added_date = []
    already_added_type = []

    for data in all_data:
        words = (data.title).split()
        for word in words:
            if len(word) > 2:
                if word not in already_added_title:
                    already_added_title.append(word)
                    Features(word=word,type='title').save()

        words = (data.address).split()
        for word in words:
            if len(word) > 2:
                if word not in already_added_address:
                    already_added_address.append(word)
                    Features(word=word,type='address').save()

        words = (data.date).split()
        for word in words:
            if len(word) > 2:
                if word not in already_added_date:
                    already_added_date.append(word)
                    Features(word=word,type='date').save()
        
        words = (data.type).split()
        for word in words:
            if len(word) > 2:
                if word not in already_added_type:
                    already_added_type.append(word)
                    Features(word=word,type='type').save()

    print('number of title features added : '  ,len(already_added_title))
    print('number of address features added : ',len(already_added_address))
    print('number of date features added : '   ,len(already_added_date))
    print('number of type features added : '   ,len(already_added_type))


def month_search(string):
    words = string.split()
    monthes = []
    for word in words:
        if word.lower() in list_of_monthes:
            index = list_of_monthes.index(word.lower())
            monthes.append(list_of_short_monthes[index])
        elif word.lower() in list_of_short_monthes:
            index = list_of_short_monthes.index(word.lower())
            monthes.append(list_of_monthes[index])
    
    return monthes