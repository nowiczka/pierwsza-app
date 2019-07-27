# -*- coding: utf-8 -*-

import sys, os, datetime,time,json, timeit,itertools, webbrowser,random, threading,pyodbc
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template, request,send_file,session
from dateutil import parser # do zmiany datetime na string
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import linecache
import sys

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
	return
	
def savefecha(item,d):
    """Return JSON file with a calculation date. Later is use in the interface to informe a user about the last calcualtion of zones/subzones"""
    with open('static/fechas.json') as data_file:    #actualizacja plikow JSON 
        d = d.strftime("%d/%m/%Y %H:%M")  
        data = json.load(data_file)
        data["fechas"][item]["fecha"]  = d
    with open('static/fechas.json', 'w') as data_file:
        data_file.write(json.dumps(data))
	return
        
def createReport(dfRaport):
    """Return PDF file with subsectors data"""
    PATH_OUT = "static/"
    dfRaport = dfRaport.round(2)
    dfRaport.columns =['Subsector','Senal','Consumo','Qmin','m3/km.dia','Ratio']
    dfRaport = dfRaport.sort_values('Ratio', axis=0, ascending=False, inplace=False, kind='quicksort', na_position='last')
    dfRaport = dfRaport.reset_index(drop=True)
    writer = pd.ExcelWriter(PATH_OUT + 'subzones.xlsx')
    dfRaport.to_excel(writer,'subzones')
    writer.save()
    pdfReportPages = PATH_OUT + 'informe.pdf'
    doc = SimpleDocTemplate(pdfReportPages, pagesize=A4)
    
    # container for the "Flowable" objects
    elements = []

    im = Image("static/images/logo.png", 1.5*inch, 0.75*inch)
    im.hAlign = 'LEFT'
    elements.append(im)

    styles = getSampleStyleSheet()
    sty = ParagraphStyle(name="myStyle", alignment=TA_RIGHT)
    elements.append(Paragraph(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), style=sty))
    elements.append(Paragraph("Caudales Minimos Nocturnos", styles['Title']))
    elements.append(Paragraph("", styles['Title']))

    # Make heading for each column and start data list
    column1Heading = 'Subsector'
    column2Heading = 'Senal'
    column3Heading = 'Consumo'
    column4Heading = 'Q min'
    column5Heading = 'm3/km.día'
    column6Heading = 'Ratio'
    

    # Assemble data for each column using simple loop to append it into data list
    data = [dfRaport.columns[:,].values.astype(str).tolist()] + dfRaport.values.tolist()

    tableThatSplitsOverPages = Table(data, [5.9 * cm, 3.0 * cm, 1.85 * cm, 1.65 * cm, 1.95 * cm, 1.70 * cm], repeatRows=1)
    tableThatSplitsOverPages.hAlign = 'LEFT'
    tblStyle = TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                           ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                           ('LINEBELOW',(0,0),(-1,-1),1,colors.black),
                           ('BOX',(0,0),(-1,-1),1,colors.black),
                           ('BOX',(0,0),(0,-1),1,colors.black)])

    tblStyle.add('BACKGROUND',(0,0),(5,0),colors.lightblue)
    tblStyle.add('BACKGROUND',(0,1),(-1,-1),colors.white)

    for i in range(len(dfRaport)):

        if dfRaport['Ratio'][i]>9999:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.gray)

        elif dfRaport['Ratio'][i]>1.7:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.red)

        elif dfRaport['Ratio'][i]>1.3:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.orange)

        elif dfRaport['Qmin'][i]==-1:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.gray)
        else:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.green)

    tableThatSplitsOverPages.setStyle(tblStyle)
    elements.append(tableThatSplitsOverPages)

    doc.build(elements)
    return
    
def createReportzones(dfRaport):
    """Return PDF file with zones data"""
    dfRaport = dfRaport.round(2)
    PATH_OUT = "static/"
    dfRaport.columns =['Sector','Q medio','Q min','Q fuga','Rendimiento'] 
    dfRaport['Rendimiento']= dfRaport['Rendimiento'].round(2)
    dfRaport = dfRaport.sort_values('Rendimiento', axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
    dfRaport = dfRaport.reset_index(drop=True)
    writer = pd.ExcelWriter(PATH_OUT + 'zones.xlsx')
    dfRaport.to_excel(writer,'zones')
    writer.save()
    pdfReportPages = PATH_OUT + 'informe_zones.pdf' 
    doc = SimpleDocTemplate(pdfReportPages, pagesize=A4)

    # container for the "Flowable" objects
    elements = []
    styles = getSampleStyleSheet()
    sty = ParagraphStyle(name="myStyle", alignment=TA_RIGHT,leading= 32)
    im = Image("static/images/logo.png", 1.5*inch, 0.75*inch)
    im.hAlign = 'LEFT'
    elements.append(im)

    fecha_calculo = (datetime.datetime.now() - datetime.timedelta(hours=24) ).strftime("%d/%m/%Y")
    
    elements.append(Paragraph(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), style=sty))
    elements.append(Paragraph("Rendimiento  hidráulico de los zones " + str(fecha_calculo), styles['Title'])) #!
    

    # Assemble data for each column using simple loop to append it into data list
    data = [dfRaport.columns[:,].values.astype(str).tolist()] + dfRaport.values.tolist()

    tableThatSplitsOverPages = Table(data, [7 * cm, 2.25 * cm, 2.25 * cm, 2.25 * cm, 3 * cm], repeatRows=1) #!
    tableThatSplitsOverPages.hAlign = 'LEFT'
    tblStyle = TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                           ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                           ('LINEBELOW',(0,0),(-1,-1),1,colors.black),
                           ('BOX',(0,0),(-1,-1),1,colors.black),
                           ('BOX',(0,0),(0,-1),1,colors.black)])

    tblStyle.add('BACKGROUND',(0,0),(4,0),colors.lightblue)
    tblStyle.add('BACKGROUND',(0,1),(-1,-1),colors.white)

    for i in range(len(dfRaport)): 

        if dfRaport['Rendimiento'][i]<0: #
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.gray)
            
        elif dfRaport['Rendimiento'][i]>100: #
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.gray)

        elif dfRaport['Rendimiento'][i]>80:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.green)

        elif dfRaport['Rendimiento'][i]>60:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.orange)

        else:
            tblStyle.add('TEXTCOLOR',(0,i+1),(-1,i+1),colors.red)


    tableThatSplitsOverPages.setStyle(tblStyle)
    elements.append(tableThatSplitsOverPages)

    doc.build(elements)


    return
    
def accessSQL():
    """
    this function connects script to database ****
    :param name: none
    :return: cursor
    """
    cnxn = pyodbc.connect("DSN=********") # Connection with a DSN (Data Source Name)
    cursor = cnxn.cursor()
    return(cursor)

def MDB():
    """
    this function connects script to database Access Driver
    :param name: none
    :return: cursor
    """
    ACCESS_DATABASE_FILE = '*********.mdb' # acesso al base de datos *******.mdb
    ODBC_CONN_STR = 'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;' % ACCESS_DATABASE_FILE
    cnxn = pyodbc.connect(ODBC_CONN_STR)
    cursor = cnxn.cursor()
    return cursor

def GetConsumption(cursor,Id,Dia):
    """Return ConsumoNocturno, ConsumoDiario for specific subsector and day"""
    # Ejecutar sentencia:
    sentenciasql = ("SELECT *FROM consumozonas WHERE id=? AND day=?")  
    cursor.execute(sentenciasql,(Id,Dia))
    row = cursor.fetchall()[0]
    ConsumoNocturno, ConsumoDiario = row[2], row[3]
    
    return ConsumoNocturno, ConsumoDiario
    
def GetUARL(cursor,tipo,ID):
    """Return el umbral mínimo de fugas (UARL) (perdidas inevitables) for specific zone """
    # Ejecutar sentencia:
    sentenciasql = ("SELECT perdidasin FROM zonappresion WHERE type=? AND id=?")
    cursor.execute(sentenciasql,(tipo,ID))
    row = cursor.fetchall()
    uarl = sum([row[i][0] for i in range(len(row))])
    
    return uarl

def GetUARLzones(cursor,ID):
    """Return uarl (perdidas inevitables) for specific sector as a sum of all its subsectors UARL  """
    
    subzonesID = Getsubzones(ID,cursor)[0]
    uarl = sum([GetUARL(cursor,'typef',subzonesID[i]) for i in range(len(subzonesID))])
    
    return uarl
    
def GetConsumptionAll(cursor,ID,dias):
    """Return consumption for a list of dates """
    AllNight = []
    AllDay = []

    for i in range(len(dias)):
        try:
            ConsumoNocturno, ConsumoDiario = GetConsumption(cursor,int(ID) ,dias[i])
        except: # si no hay ningun dato, por defecto asignamos 0
            ConsumoNocturno, ConsumoDiario =[0,0]
            
        AllNight.append(ConsumoNocturno)
        AllDay.append(ConsumoDiario)
        
    return AllNight,AllDay
    
def GetConsumptionSector(idzh,cursor,date_list):
    """Return Consumption for specific sector for whole week   """
    subzonesID = Getsubzones(idzh,cursor)[0] 

    dfCN =  pd.DataFrame([], index=date_list) # dataframe para consumo nocturno
    dfCD =  pd.DataFrame([], index=date_list)# dataframe para consumo diario


    for i in range(len(subzonesID)): # para cada subsector cogemos consumos para cada dia de la ultima semana : date_list

        ConsumoNocturno, ConsumoDiario = GetConsumptionAll(cursor,subzonesID[i],date_list)
        dfCN[subzonesID[i]] = ConsumoNocturno
        dfCD[subzonesID[i]] = ConsumoDiario

    if len(subzonesID)>1: # si tenemos mas que un subsector, hacemos suma de todos subzones

        dfCD['Total'] = dfCD.sum(axis=1)
        dfCN['Total'] = dfCN.sum(axis=1)

    else: # si tenemos solo un subsector, devolvemos valores solo de este subsector
        ConsumoNocturno, ConsumoDiario = GetConsumptionAll(cursor,idzh,date_list)
        dfCN['Total'] = ConsumoNocturno
        dfCD['Total'] = ConsumoDiario

    NocturnoGlobal = [dfCN['Total'].iat[kk] for kk in range(len(dfCN['Total']))] # cambio de df a una lista
    DiarioGlobal = [dfCD['Total'].iat[kk] for kk in range(len(dfCD['Total']))] # cambio de df a una lista


    return NocturnoGlobal , DiarioGlobal

def Getsubzones(idzh,cursor): 
    """
    this function gets subsectors ID and names of selected sector script to database Access Driver
    :param name: idzh ,cursor --->MDB()
    :return: subzonesID,subzonesNombres
    """
    sentenciasql = ("SELECT * FROM zonaspresion WHERE type='typef' AND [idzh]=?")
    cursor.execute(sentenciasql,(idzh))
    row = cursor.fetchall()
    subzonesID = [i[0] for i in row]
    subzonesNombres = [i[1] for i in row]
    
    return subzonesID, subzonesNombres
    
def GetLongitudRed(ID):
    """
    this function gets subsectors 'logitud de la red' in order to calculate ratio ( Q min /24h * XX km)
    :param name: ID 
    :return: longitud ( type: float)
    """
    cursor = MDB() # database.mdb'
    sentenciasql = ("SELECT longred FROM zonapresion WHERE type=typef AND [ID]=?")
    cursor.execute(sentenciasql,(ID))
    longitud = cursor.fetchall()[0][0]
    return longitud
    
def GetNombreZona(idzh,cursor):
    """
    this function gets name of sector 
    :param name: idzh ,cursor --->MDB()
    :return: NombreZona
    """
    cursor.execute("select Nombre as zmienna from zonapresion where [ID]= ?",idzh) # cambio desde ID ZH a ID para poder coger el nombre del subector tambien. Resulta que ID del sector = idzh de este sector
    row = cursor.fetchone()
    NombreZona = row.zmienna
    try:
        NombreZona = NombreZona.decode('utf_8')
    except:
        pass
    return NombreZona 

def GetContadoresAndSignos(ID,cursor):
    """
    this function gets contadores and signos of sector from table contazonaspres
    signo means the sign of the contador in case of balance if it enters/exits into/from sector
    :param name: ID ,cursor --->MDB()
    :return: contadores,signos
    """
    sentenciasql = ("SELECT Contador, Signo FROM contazonaspres WHERE agrup = %s" % ID)
    cursor.execute(sentenciasql)
    rows = cursor.fetchall()
    contadores = [int(rows[i][0]) for i in range(len(rows))]
    signos = [rows[i][1] for i in range(len(rows))]
    return contadores,signos
    
def GetSenal(contadores,cursor): 
    """
    this function gets senales(analogica/digital) and codigos of sector from table indexport
    if codigo =! contador ---> contador tiene un inverso (senal digital). Mira la funcion GetQmedioAnalogica
    :param name: contadores ,cursor --->MDB()
    :return: senales,codigos
    """
    senales,codigos = [],[]

    for i in range(len(contadores)):
        sentenciasql = "SELECT * FROM indexport WHERE ncont= %s" % contadores[i]
        cursor.execute(sentenciasql)
        rows = cursor.fetchall()
        try:
            senales.append(str(rows[0][1]))
            codigos.append(int(rows[0][0]))
        except Exception as e: # cuando el contador no tiene asignado ningun senal, le ponemos error. Es importante porque luego quitamos este contador del balance
            senales.append('error'+str(contadores[i]))
            codigos.append(9999)
       
            
    return senales,codigos

def GetSenalTotal(contador,cursor):
    """
    this function gets senales totalizados and a FactorCT  from table indexport
    FactorCT usually is 1, but there are some values equal 10 (cuando el senal esta mal escalado)
    :param name: contador,cursor --->MDB()
    :return: senales,FactorCT
    """
    sentenciasql =("SELECT Totalizado FROM [indexport] WHERE ncont=?")
    cursor.execute(sentenciasql,contador)
    row = cursor.fetchall()
    senales = row[0]
    senales = senales[0].replace(" ", "") # en la base de datos unos senales se terminan con un espacio. Hay que quitarlo
  
    # FactorCT : importante en el caso de senales mal escalados. En la mayoria, es igual a 1...una pequena trampa que a lo mejor pronto nos sea importante y se pueda borrar  
    sentenciasql =("SELECT FactorCT FROM [indexport] WHERE ncont=?")
    cursor.execute(sentenciasql,contador)
    row = cursor.fetchall()
    FactorCT = row[0][0] 
    
    return(senales,FactorCT)

def GetFlow(SenalAnalogica,FechaInicio,FechaFinal,cursor):
    """
    this function gets flow of senal analogica from bbdd
    :param name: SenalAnalogica,FechaInicio,FechaFinal,cursor --->accessSQL()
    :return: Qdir,fechasQdir 
    """
    sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora between ? and ? and qid=984561")
    cursor.execute(sentenciasql,(SenalAnalogica,FechaInicio,FechaFinal))
    row =cursor.fetchall()
    Qdir = [row[i][3] for i in range(len(row))]
    Qdir = [row[i][3] for i in range(len(row))]
    fechasQdir = [row[i][2] for i in range(len(row))]
    return Qdir,fechasQdir

def GetFlowTotal(SenalTotal,FechaInicio,FechaFinal,cursor):
    """
    this function gets flow of senal total from databse between two dates: FechaInicio,FechaFinal
    :param name: SenalTotal,FechaInicio,FechaFinal,cursor --->accessSQL()
    :return: Qdir,fechasQdir 
    """
    sentenciasql=("SELECT * FROM numerictable WHERE tn=? and fechahora between ? and ? and qid=984561")
    cursor.execute(sentenciasql,(SenalTotal,FechaInicio,FechaFinal))
    row = cursor.fetchone()
    
    try: # buscamos algun dato de este dia
        Qtot,fechasQtot = row[3],row[2] 
    except:
        try: # si no hay ningun dato de este dia, cogemos el ultimo dato disponible
            # seria guay usar funcion LAST y aumentar la rapidez de los calculos, pero parece que no este disponible en pyodbc, Python
            sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora < ? and qid=984561")
            cursor.execute(sentenciasql,(SenalTotal,FechaInicio))
            row = cursor.fetchall()
            Qtot = row[-1][3]
            fechasQtot = row[-1][2] 
        except: # si no hay ningun dato devolvemos [] para que luego coge el senal analogica
            Qtot = []
            fechasQtot = []
            
    return Qtot,fechasQtot
    
def GetFlowD(senalDigital,FechaInicio,FechaFinal,cursor):
    """
    this function gets flow of senal digital from bbdd
    :param name: senalDigital,FechaInicio,FechaFinal,cursor --->accessSQL()
    :return: Qinv,fechasQinv
    """
    sentenciasql=("SELECT * FROM dsv WHERE tn=? and fechahora between ? and ? and qid=984561")
    cursor.execute(sentenciasql,(senalDigital,FechaInicio,FechaFinal))
    row =cursor.fetchall()
    Qinv = [row[i][3] for i in range(len(row))]
    try: # iteracja wymaga min len = 2
        Qinv = map(lambda x: 1 if x else 0, Qinv) # cambio boolean a intiger: True = 1, False= 0
    except: # mamy tylko jedna wartosc
        Qinv = int(Qinv)
        
    fechasQinv = [row[i][2] for i in range(len(row))]
    
    return Qinv, fechasQinv
    
def GetQDigitalFromTheDateBefore(cursor,senalDigital,FechaInicio):
    TheLastDate = FechaInicio - datetime.timedelta(seconds=1)
    sentenciasql=("SELECT valor as zmienna FROM dsv WHERE tn=? and fechahora < ? and qid=984561")
    cursor.execute(sentenciasql,(senalDigital,TheLastDate))
    row =cursor.fetchall()[-1]
    Q = row.zmienna
    try:  # iteracja wymaga min len = 2
        Q = map(lambda x: 1 if x else 0, Q)
    except: # mamy tylko jedna wartosc
        Q = int(Q)
    return Q
    
def GetQDigitalFromTheDateAfter(cursor,senalDigital,FechaFinal):
    sentenciasql=("SELECT valor as zmienna FROM dsv WHERE tn=? and fechahora > ? and qid=984561")
    cursor.execute(sentenciasql,(senalDigital,FechaFinal))
    row =cursor.fetchone()[-1]
    Q = row.zmienna
    try:  # iteracja wymaga min len = 2
        Q = map(lambda x: 1 if x else 0, Q)
    except: # mamy tylko jedna wartosc
        Q = int(Q)
    return Q
    
############################################## Resampling&Interpolation
def Resample(date_stngs,intervalo,Q,FechaInicio,FechaFinal):
    """
    this function interpolates timeseries data using new time vector
    :param name: date_stngs(dates from database),intervalo(noramlly 10Min),Q (flow from database),FechaInicio,FechaFinal
    :return: rs['Values']
    """
    date_times = pd.to_datetime(pd.Series(date_stngs))
    df = pd.DataFrame(data={'Values': Q}, index=date_times)
    #estructura vacia con indices deseados
    #rs = pd.DataFrame(index=df.resample(intervalo).iloc[x:y].index)
    x  = pd.date_range(FechaInicio, FechaFinal, freq=intervalo).shift(0, freq=pd.datetools.day)
    rs = pd.DataFrame(index=x) ####
    # matriz de indices que corresponden al de mas cercanos tiempos despues del cambio de las horas
    idx_after = np.searchsorted(df.index.values, rs.index.values)
    # valores y pasos del tiempo antes/despues del cambio de las horas
    rs['after'] = df.loc[df.index[idx_after], 'Values'].values
    rs['before'] = df.loc[df.index[idx_after - 1], 'Values'].values
    rs['after_time'] = df.index[idx_after]
    rs['before_time'] = df.index[idx_after - 1]
    # calculo del nuevo valor
    rs['span'] = (rs['after_time'] - rs['before_time'])
    rs['after_weight'] = (rs['after_time'] - rs.index) / rs['span']
    rs['before_weight'] = (pd.Series(data=rs.index, index=rs.index) - rs['before_time']) / rs['span']
    rs['Values'] = rs.eval('after * before_weight + before * after_weight') 

    return(rs['Values'])

def ResampleDIGITAL(date_stngs,intervalo,Q,FechaInicio,FechaFinal):
    """
    this function returns data with step changes, no interpolation is done 
    :param name: date_stngs(dates from database),intervalo(noramlly 10Min),Q (flow from database),FechaInicio,FechaFinal
    :return: rs['Values']
    """
    date_times = pd.to_datetime(pd.Series(date_stngs))
    df = pd.DataFrame(data={'Values': Q}, index=date_times)

    x  = pd.date_range(FechaInicio, FechaFinal, freq=intervalo).shift(0, freq=pd.datetools.day)
    rs = pd.DataFrame(index=x) 
    # matriz de indices que corresponden al de mas cercanos tiempos despues del cambio de las horas
    idx_after = np.searchsorted(df.index.values, rs.index.values)
    # valores y pasos del tiempo antes/despues del cambio de las horas
    rs['Values'] = df.loc[df.index[idx_after - 1], 'Values'].values
    
    return(rs['Values'])

def InsertValues(FechaInicio,FechaFinal,date_stngs,Q,tabla,Senal,cursor):
    time = [FechaInicio,FechaFinal] 

    if time[0] < date_stngs[0]: # si Fecha Inicio es antes que la primera fecha del bbdd 

        try:#analogica
            Q_new,NewFecha = GetQFromTheDateBefore(cursor,Senal,time[0])
        except:#cuando no hay datos
            Q_new,NewFecha =  Q[0],time[0]

        date_stngs.insert(0,NewFecha)
        Q.insert(0,Q_new) # 


    if time[1] > date_stngs[-1]:# si Fecha Final es despues de la ultima fecha del bbdd

        try:#analogica
            Q_new,NewFecha = GetQFromTheDateAfter(cursor,Senal,FechaFinal)
        except:#cuando no hay datos
            Q_new,NewFecha = Q[-1],time[1]

        date_stngs.append(NewFecha)
        Q.append(Q_new) # cogemos el primero valor del dia siguiente 

    return(time,date_stngs,Q)

def InsertValuesDIGITAL(FechaInicio,FechaFinal,date_stngs,Q,tabla,Senal,cursor):

    time = [FechaInicio,FechaFinal] 

    if time[0] < date_stngs[0]: # si Fecha Inicio es antes que la primera fecha del bbdd 

        try:#analogica
            Q_new,NewFecha = GetQDigitalFromTheDateBefore(cursor,Senal,time[0])
        except:#cuando no hay datos
            Q_new,NewFecha =  Q[0],time[0]

        date_stngs.insert(0,NewFecha)
        Q.insert(0,Q_new) # 

    if time[1] > date_stngs[-1]:# si Fecha Final es despues de la ultima fecha del bbdd

        Q_new,NewFecha = Q[-1],time[1]
        date_stngs.append(NewFecha)
        Q.append(Q_new) # cogemos el primero valor del dia siguiente 

    return(time,date_stngs,Q)
    
########################### Caudal Medio
def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data)/float(n) 

def _ss(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    ss = sum((x-c)**2 for x in data)
    return ss

def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    ss = _ss(data)
    pvar = ss/n # the population variance
    return pvar**0.5

def CleanData(data):
    """replacement of the values with a different sign than most by the values of the preceding day  """
    correcion =[]
    
    # sprawdzamy jaki zank jest poprawny dla danego SYGNALU
    for i in range(len(data)): 
        if data[i]>=0:
            correcion.append(1)
        elif data[i]<0:
            correcion.append(0)
            
    # bierzemy wartosc z dnia poprzedniego dla wartosci innych niz SignoCorrecto
    if sum(correcion)>=len(data)/2:
        SignoCorrecto = 1
    elif sum(correcion)<len(data)/2:
        SignoCorrecto = 0
        
    for ii in range(len(correcion)):
        if correcion[ii]!=SignoCorrecto:
            data[ii] = data[ii-1]
            
    
            
    return(data)

def ResetTotal(cursor,SenalTotal,FechaInicio,FechaFinal):
    """importante when SenalTotal reches its limites during a day."""
    sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora between ? and ? and qid=984561")
    cursor.execute(sentenciasql,(SenalTotal,FechaInicio,FechaFinal))
    row = cursor.fetchall()
    Qtot = [i[3] for i in row]
    fechasQtot = [i[2] for i in row]

    deltaQtot = [Qtot[i]-Qtot[i-1] for i in range(1,len(Qtot))]

    indeksy = [deltaQtot.index(i) for i in deltaQtot if i<0] 
    indeksy.append(len(deltaQtot)) # jezeli sie zeruje na ostatnim znaku? tez trzeba wziac dane z kolejnego dnia..... albo analogica ;D

    partes = []

    if indeksy[0]!=0:
        indeksy.insert(0,0)
        j = 0

    elif indeksy[0] == 0:
        sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora < ? and qid=984561")
        cursor.execute(sentenciasql,(SenalTotal,FechaInicio))
        row = cursor.fetchall() #fajnie by bylo wziac ostatni elemet od razu ale nie wiem jak
        Qtot_add = [i[3] for i in row]
        j = 1

        partes.append(Qtot[0] - Qtot_add[-1])


    for i in range(len(indeksy)-1-j): # w zaleznosci ile razy segnal zerowal sie w ciagu rozpatrzanych 24 godzin

        if j == 0 and i ==0:

            partes.append(Qtot[indeksy[i+1]]-Qtot[indeksy[i]]) #zobacz notakte z 19/07 
            partes.append(Qtot[indeksy[i+1]+1])
        else: 
            partes.append(Qtot[indeksy[i+1]]-Qtot[indeksy[i]+1])    #funciona para este que se reseta unas veces al dia

    return sum(partes)

def GetQmedio(SenalTotal,FechaInicio,FechaFinal):
    """returns flow for a specific signal and a specific day """

    cursor = accessSQL()
    date_times = pd.date_range(FechaInicio, FechaFinal, freq='D')
    Qtot,deltaQ = [],[]
    FechaFinal = FechaInicio + datetime.timedelta(days=1)
    Q,fecha = GetFlowTotal(SenalTotal,FechaInicio,FechaFinal,cursor)
    Qtot.append(Q) # wartosc dla pierwszego dnia
    FechaInicio += datetime.timedelta(days=1)
    
    for i in range(0,len(date_times)):

        FechaFinal = FechaInicio + datetime.timedelta(hours=24)
        Q,fecha = GetFlowTotal(SenalTotal,FechaInicio,FechaFinal,cursor)
        Qtot.append(Q) # wartosc dla drugiego dnia
        
        if abs(Qtot[i+1]-Qtot[i])<90000: # porownianie obu wartosci
            deltaQ.append(Qtot[i+1]-Qtot[i]) 
            
        elif abs(Qtot[i+1]-Qtot[i])>=90000:
            FechaInicio -= datetime.timedelta(days=1)
            FechaFinal = FechaInicio + datetime.timedelta(hours=24)
            delta = ResetTotal(cursor,SenalTotal,FechaInicio,FechaFinal)
            deltaQ.append(delta)
            FechaInicio += datetime.timedelta(days=1)

        FechaInicio += datetime.timedelta(days=1)
 
    deltaQ = CleanData(deltaQ) # usuwamy sospecious data


    #df = pd.DataFrame(data={SenalTotal: deltaQ}, index=date_times)

    return deltaQ,SenalTotal

def TieneInverso(codigos,contador,senales,FechaInicio,FechaFinal,cursor,intervalo,tsDIR,znak):
    """ This is a part of  GetQmedioAnalogica(SenalAnalogica,FechaInicio,FechaFinal,idzh,contador) """
   
    indeks =codigos.index(-1*contador) # cogemos el indice del contador
    senalDigital = senales[indeks] # cogemos senal digital del contador

    Qinv, fechasQinv = GetFlowD(senalDigital,FechaInicio,FechaFinal,cursor)
    
    if Qinv == []:

        try:
            Q_zastepcze = GetQDigitalFromTheDateBefore(cursor,senalDigital,FechaInicio)
        except Exception as e:
            Q_zastepcze = 1
        fechasQinv,Qinv =[FechaInicio,FechaFinal] ,[Q_zastepcze, Q_zastepcze]
        
    else:
            InputData = InsertValuesDIGITAL(FechaInicio,FechaFinal,fechasQinv,Qinv,'dsv',senalDigital,cursor)                     
            fechasQinv,Qinv = InputData[1],InputData[2]


    tsINV = ResampleDIGITAL(fechasQinv,intervalo,Qinv,FechaInicio,FechaFinal)  

    x  = pd.date_range(FechaInicio, FechaFinal, freq='10Min').shift(0, freq=pd.datetools.day)
    Q = [(-2*tsINV[i]+1)*tsDIR[i]*znak for i in range(len(tsDIR))] # obliczanie nowych wartosci Q
    
    return Q
    
def GetQmedioAnalogica(SenalAnalogica,FechaInicio,FechaFinal,idzh,contador):
    """ the function is used when SenalTotal has no value or it doesn't exist for a specific contador"""
    date_times,intervalo = pd.date_range(FechaInicio, FechaFinal, freq='D'),'10Min'
   
    cursor = MDB() # acesso al base de datos database.mdb
    contadores, signo = GetContadoresAndSignos(idzh,cursor) # Cogemos info de los contadores y signos de la zona
    senales, codigos = GetSenal(contadores,cursor) # Cogemos info de los senales y codigos de los contadores de la zona
    indeks = contadores.index(contador)  # buscamos el index del contador que tenga el SenalAnalogica en la lista de todos contadores
    znak = signo[indeks] # cogemos el signo de este contador
    
    cursor = accessSQL() ########## SQL ########
    Qmedio =[] 

    for jj in range(len(date_times)): # bucle para cada dia para un contador
        FechaFinal = FechaInicio + datetime.timedelta(hours=24) 
    
        Qdir, fechasQdir = GetFlow(senales[indeks],FechaInicio,FechaFinal,cursor)

        if Qdir ==[]: #jesli nie ma zadnych danych por defecto cogemos 0
            Qdir,fechasQdir =[0,0],[FechaInicio,FechaFinal]
            
        try:
            InputData = InsertValues(FechaInicio,FechaFinal,fechasQdir,Qdir,'numsampv',senales[indeks],cursor)
            fechasQdir, Qdir = InputData[1], InputData[2]
        except:
            pass
        
        tsDIR = Resample(fechasQdir,intervalo,Qdir,FechaInicio,FechaFinal) 

        ########### procedimiento en el caso de inverso
        if -1*contador in codigos:
            Q = TieneInverso(codigos,contador,senales,FechaInicio,FechaFinal,cursor,intervalo,tsDIR,znak)

        # si no tenemos inverso cogemos el valor de Qdir directamente
        elif -1*contador not in codigos:
            Q = [tsDIR[i]*znak for i in range(len(tsDIR))] # obliczanie nowych wartosci Q
            
        Qmedio.append((np.trapz(Q))/6) # time series para un contador bo liczymy dla kazdych 10 minut czyli dzielim przez 6

        FechaInicio = FechaInicio + datetime.timedelta(hours=24) 
        
    Qmedio = CleanData(Qmedio)
    return Qmedio
  
def CuandoFallaTot(contador,cursor,contadoresToremove,Qmedio,SenalTotal,idzh,FechaInicio,FechaFinal):
    """ the function is used when SenalTotal has no value or it doesn't exist for a specific contador"""
    """ it remove contador if senal analogica neither has  value nor it exists for a specific contador"""
    SenalAnalogica, Codigo = GetSenal([contador],cursor) 
    if SenalAnalogica[0] =='error'+str(contador):
        contadoresToremove.append(contador)
    elif SenalAnalogica[0] !='error'+str(contador): 
        caudal_medio = GetQmedioAnalogica(SenalAnalogica[0],FechaInicio,FechaFinal,idzh,contador)
    try:
        Qmedio.append(caudal_medio)
        SenalTotal.append(SenalAnalogica[0])
    except: #hay algun problema con el senal: es digital o no tiene valores'
        contadoresToremove.append(contador)
        
    return(contadoresToremove,Qmedio,SenalTotal)

def zonesQmedio(idzh,FechaInicio,FechaFinal):
    """ returns average flow for a week (between fechaInicio and FechaFinal) for a specific sector """
    # acesso al base de datos database.mdb
    cursor = MDB()
    until = int((FechaFinal  - FechaInicio).total_seconds()  / 3600 / 24 + 1)
    date_list = [FechaInicio + datetime.timedelta(days=x) for x in range(0, until)]

    #Cogemos Nombre de la zona usando idzh
    NombreZona = GetNombreZona(idzh,cursor)

    #Cogemos contadores del sector
    contadores, signos = GetContadoresAndSignos(idzh,cursor) 
    SenalTotal, Qmedio,contadoresToremove = [],[],[] 
    for i in range(len(contadores)): # bucle para cada contador
        contador,signo = contadores[i], signos[i]

        try:
            senales,FactorCT = GetSenalTotal(contador,cursor)
  
            if senales[1]== str(9): 
                contadoresToremove.append(contador)
            elif senales[1]!=str(9):  
                caudal_medio = GetQmedio(senales,FechaInicio,FechaFinal) 
                
                if caudal_medio == [] or pstdev(caudal_medio[0])/mean(caudal_medio[0]) > 2: # si no hay datos para la senal o los datos son muy raros, la quitamos del balance
                    contadoresToremove,Qmedio,SenalTotal = CuandoFallaTot(contador,cursor,contadoresToremove,Qmedio,SenalTotal,idzh,FechaInicio,FechaFinal)
                else:
                    Qmedio.append(signo*caudal_medio[0]*FactorCT)
                    SenalTotal.append(caudal_medio[1])

        except:
            SenalAnalogica, Codigo = GetSenal([contador],cursor) 
            contadoresToremove,Qmedio,SenalTotal = CuandoFallaTot(contador,cursor,contadoresToremove,Qmedio,SenalTotal,idzh,FechaInicio,FechaFinal)
    contadores = [x for x in contadores if x not in contadoresToremove] 
   
    df = pd.DataFrame( [],index=date_list)   

    
    for jj in range(0,len(contadores)): 
        df[SenalTotal[jj]] = Qmedio[jj]

    df['Total'] = df.sum(axis=1)/24
    
    return df

######################### caudal minimo
def GetQFromTheDateBefore(cursor,SenalAnalogica,FechaInicio):
    TheLastDate = FechaInicio - datetime.timedelta(seconds=1)
    sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora < ? and qid=984561")
    cursor.execute(sentenciasql,(SenalAnalogica,TheLastDate))
    row =cursor.fetchall()[-1]
    Q = row[-2]
    fecha = row[-3]
    return Q,fecha
 
def GetQFromTheDateAfter(cursor,SenalAnalogica,FechaFinal):
  
    sentenciasql=("SELECT * FROM numsampv WHERE tn=? and fechahora > ? and qid=984561")
    cursor.execute(sentenciasql,(SenalAnalogica,FechaFinal))
    row =cursor.fetchone()[-1]
    Q = row[-2]
    fecha = row[-3]
    return Q,fecha
    
def GetQmin(FechaInicio,FechaFinal,SenalAnalogica,znak):

    ################# connect to bbdd
    cursor = accessSQL()

    date_times= pd.date_range(FechaInicio, FechaFinal, freq='D')
    FechaInicio = FechaInicio + datetime.timedelta(hours=1.5)

    Qmin = []

    for i in range(len(date_times)):
        FechaFinal = FechaInicio + datetime.timedelta(hours=3.5)

        Q, horas = GetFlow(SenalAnalogica,FechaInicio,FechaFinal,cursor)
        
        if not Q:
            FechaFinal2 = FechaInicio 
            FechaInicio2 = FechaInicio - datetime.timedelta(hours=24)
            try:

                Q, horas = GetFlow(SenalAnalogica,FechaInicio2,FechaFinal2,cursor)

                Qmin.append(Q[-1])
            except Exception as e:
                Qmin.append(0.01) #!!!!!!!!!!!!!! Si no tenemos valores cogemos 0.01 por defecto
                
        elif  Q:
            Q_opcional = GetQFromTheDateBefore(cursor,SenalAnalogica,FechaInicio)[0] # 
            Qmin.append(min(min(Q),Q_opcional)*znak)

        FechaInicio += datetime.timedelta(days=1)

    df = pd.DataFrame(data={SenalAnalogica: Qmin}, index=date_times)
    

    return df

def balanceQmin(ID,FechaInicio,FechaFinal):

    ######################################################################
    numero_dias = pd.date_range(FechaInicio, FechaFinal, freq='D')
    intervalo = '10Min'
    FechaInicio = FechaInicio + datetime.timedelta(hours=1.5) # calculamos minimo entre 1:30 y 5:00

    cursor = MDB() # conexión con el database.mdb

    contadores, signo = GetContadoresAndSignos(ID,cursor) # Cogemos info de los contadores y signos de la zona
    senales, codigos = GetSenal(contadores,cursor) # Cogemos info de los senales y codigos de los contadores
    Codigos = np.asarray(codigos)  # cambio de la lista codigos a array para poder detectar cunatos inversos tenemos

    ## indices to remove
    remove_indices = [i for i,x in enumerate(senales) if x == 'error'+str(contadores[i])]

    if remove_indices !=[]:
        contadores = [i for j, i in enumerate(contadores) if j not in remove_indices]
        signo = [i for j, i in enumerate(signo) if j not in remove_indices]
        senales = [i for j, i in enumerate(senales) if j not in remove_indices]
        Codigos = [i for j, i in enumerate(Codigos) if j not in remove_indices]

    # devuelva los indices de los senales analogicas
    IndAnalogicos= np.where(Codigos > 0)[0]
        
    ########## SQL ########
    cursor = accessSQL()

    Qmin=[]


    for jj in range(len(numero_dias)): # bucle para cada dia: cada dia tiene su propio balance entr 2:00-5:00
        FechaFinal = FechaInicio + datetime.timedelta(hours=3.5) 

        x  = pd.date_range(FechaInicio, FechaFinal, freq=intervalo).shift(0, freq=pd.datetools.day)
        dfDiario = pd.DataFrame( [], index=x)

        for i in range(len(IndAnalogicos)):# bucle para cada senal del sector

            contador, znak = contadores[IndAnalogicos[i]], signo[i]
            
            SenalAnalogica = senales[IndAnalogicos[i]] # cogemos Caudal y Fechas para el senal analogico
    
            Qdir, fechasQdir = GetFlow(SenalAnalogica,FechaInicio,FechaFinal,cursor)
            
            try:
                QdirADD,fechasQdirADD = GetQFromTheDateBefore(cursor,SenalAnalogica,FechaInicio)
                Qdir.insert(0, QdirADD)
                fechasQdir.insert(0, fechasQdirADD)
            except: # cunado no existe ningun dato en database para esta senal
                pass
                
            if Qdir ==[]:#
                Q_zastepcze = 0.01
                fechasQdir, Qdir =[FechaInicio,FechaFinal] ,[Q_zastepcze, Q_zastepcze]

            else:

                InputData = InsertValues(FechaInicio,FechaFinal,fechasQdir,Qdir,'numsampv',SenalAnalogica,cursor)
                fechasQdir, Qdir = InputData[1], InputData[2]

            tsDIR = Resample(fechasQdir,intervalo,Qdir,FechaInicio,FechaFinal) 

            ########### procedimiento en el caso de inverso
            if -1*contador in codigos:
   
                indeks =codigos.index(-1*contador) # cogemos el indice del contador
                senalDigital = senales[indeks] # cogemos senal digital del contador

                Qinv, fechasQinv = GetFlowD(senalDigital,FechaInicio,FechaFinal,cursor)
                df_temporal = pd.DataFrame(data={'DÍA '+str(i)+ ' '+senalDigital: Qinv}, index=fechasQinv)


                if Qinv ==[]:# 

                    try:
                        Q_zastepcze = GetQDigitalFromTheDateBefore(cursor,senalDigital,FechaInicio)
                    except Exception as e:

                        Q_zastepcze = 1

                    fechasQinv,Qinv =[FechaInicio,FechaFinal] ,[Q_zastepcze, Q_zastepcze]

                else:
                    InputData = InsertValuesDIGITAL(FechaInicio,FechaFinal,fechasQinv,Qinv,'dsv',senalDigital,cursor)                     
                    fechasQinv,Qinv = InputData[1],InputData[2]


                tsINV = ResampleDIGITAL(fechasQinv,intervalo,Qinv,FechaInicio,FechaFinal)   

                Q = [(-2*tsINV[i]+1)*tsDIR[i]*znak for i in range(len(tsDIR))] # obliczanie nowych wartosci Q

                for i in range(len(tsINV)): # zmiana wartosci w timeseries
                    tsINV[i]=Q[i]

                tsFinal = tsINV # time series para un contador



            # si no tenemos inverso cogemos el valor de Qdir directamente
            elif -1*contador not in codigos:
                tsFinal = tsDIR*znak 

            dfDiario.loc[:,contador] = tsFinal
        dfDiario['Total'] = dfDiario.sum(axis=1) # to musi byc poza petla

        FechaInicio += datetime.timedelta(days=1)       
        Qmin.append(min(dfDiario['Total']))

    #SI CAUDAL MINIMO <0 =======> CAUDAL MINIM = 0
    Qmin = [x if x > 0 else 0 for x in Qmin] 

    df = pd.DataFrame(data={ID: Qmin}, index=numero_dias)

    return df

def RutaMinimum(idzh,date_times,FechaInicio,FechaFinal):
    cursor = MDB()
    df = pd.DataFrame( [], index=date_times)
    contadores,signos = GetContadoresAndSignos(idzh,cursor)

    #1. SECTOR tiene solo un caudalimetro
    if len(contadores) == 1:

        senales, codigos = GetSenal(contadores,cursor) 

        if senales:
            df[str(int(idzh))] = GetQmin(FechaInicio,FechaFinal,senales[0],signos[0])
            UARL =  GetUARL(cursor,'typef',idzh)
            df.ix[df[str(int(idzh))] == 0.01, str(int(idzh))] = UARL
        elif not senales:
             pass
    #2. SECTOR tiene mas que un caudalimetro- hay que hacer  el balance 

    elif len(contadores) != 1:

        try:
            df[str(int(idzh))] = balanceQmin(idzh,FechaInicio,FechaFinal)

        except:
            pass
            
    return df
        
def zonesQmin(idzh,FechaInicio,FechaFinal,date_times):
    cursor = MDB() # acesso al base de datos database.mdb

    subzonesID,subzonesNombres = Getsubzones(idzh,cursor)

    if subzonesID == [] or len(subzonesID) == 1:
    
        df = RutaMinimum(idzh,date_times,FechaInicio,FechaFinal)

    elif len(subzonesID)>1:
        df = pd.DataFrame( [], index=date_times)
        for i in range(len(subzonesID)):
           
            try:
                valores = RutaMinimum(subzonesID[i],date_times,FechaInicio,FechaFinal)
                df.loc[:,str(int(subzonesID[i]))] = valores
            except Exception as e:
             
                UARL =  GetUARL(cursor,'typef',subzonesID[i])
                valores = [UARL for ii in range(len(date_times))]
                df.loc[:,str(int(subzonesID[i]))] = valores
                

        df[str(idzh)] = df.sum(axis=1) 
        
    return df

#
def CreateAwsomePlot(NombreSector,date_list4graphs,medio,minimum,ratio,ObjectID,Fuga):
    ecj_data = open("static/subwebs/graphs/x.html",'rb').read()
    soup = BeautifulSoup(ecj_data)
    soup = BeautifulSoup(str(soup).replace("NOMBRE", NombreSector.encode('utf-8')))
    soup = BeautifulSoup(str(soup).replace("DIAS", str(date_list4graphs)))
    soup = BeautifulSoup(str(soup).replace("VALORES_MEDIO", str(medio)))
    soup = BeautifulSoup(str(soup).replace("VALORES_MINIMO", str(minimum) ))
    soup = BeautifulSoup(str(soup).replace("VALORES_RATIO", str(ratio) ))
    soup = BeautifulSoup(str(soup).replace("VALORES_FUGA", str(Fuga) ))

    html = soup.prettify("utf-8")

    with open("static/subwebs/graphs/"+str(ObjectID)+".html", "wb") as file:
        file.write(html)

    return
    
def CreateAwsomePlotSS(NombreSubSector,date_list4graphs,minimum,ObjectID,consumo_nocturno,fuga):

    ecj_data = open("static/subwebs/graphs/y.html",'rb').read()
    soup = BeautifulSoup(ecj_data)

    soup = BeautifulSoup(str(soup).replace("NOMBRE", NombreSubSector))
    soup = BeautifulSoup(str(soup).replace("DIAS", str(date_list4graphs)))
    soup = BeautifulSoup(str(soup).replace("CONSUMO_NOCTURNO", str(consumo_nocturno))) 
    soup = BeautifulSoup(str(soup).replace("CONSUMO_ULTIMO", str(consumo_nocturno[-1]))) 
    soup = BeautifulSoup(str(soup).replace("VALORES_MINIMO", str(minimum) ))
    soup = BeautifulSoup(str(soup).replace("VALORES_FUGA", str(fuga) ))
    

    html = soup.prettify("utf-8")

    with open("static/subwebs/graphs/SS"+str(ObjectID)+".html", "wb") as file:
        file.write(html)


    return

def CreateAwsomePlotAnual(medio_anual,fuga_anual):
    ecj_data = open("static/subwebs/graphs/bar-pattern.html",'rb').read()
    soup = BeautifulSoup(ecj_data)
    soup = BeautifulSoup(str(soup).replace("VALORES_MEDIO", str(medio_anual)))
    soup = BeautifulSoup(str(soup).replace("VALORES_FUGA", str(fuga_anual) ))

    html = soup.prettify("utf-8")

    with open("static/subwebs/graphs/bar.html", "wb") as file:
        file.write(html)

    return
    
#############################################################################
def JSONtoJS(name):

    """
    this function write JSON data to JS file
    :param name: subzonesData o zonesData
    :return: subzonesData.js o zonesData.js
    """
    txt = open('static/subwebs/uploads/'+name+".geojson")
    data = txt.read()

    #utworzenie JS na podstawie JSON
    with open('static/subwebs/uploads/'+name+".js", "w") as myfile:
        myfile.write("var "+name+" =")
        myfile.write(data)
        myfile.write(";")
        myfile.close()

    return

###################### 2. OBTENCION DE LOS DATOS DEL ARCHIVO JSON #########################
def GetInfoJSONzones(path):
    with open(path) as f:
        data_zones = json.load(f)

    name,ST_ID,ObjectID = [],[],[]

    for feature in data_zones['features']:
        name.append(feature['properties']['ST_NOMBRE'])
        ST_ID.append(feature['properties']['ST_ID'])
        ObjectID.append(feature['properties']['OBJECTID'])

    return(data_zones,ObjectID,name,ST_ID)

###############################################################################################
def funcion_global():
    start = timeit.default_timer() # para calcular el tiempo de los caculos
    cursor = MDB() # acesso al base de datos database.mdb
    ###################### 1. ESTABLECER LAS FECHAS DE CALCULO (LA ULTIMA SEMANA) #################

    d = datetime.datetime.now()    
    savefecha(0,d)
    FechaFinal = datetime.datetime(getattr(d,'year'), getattr(d,'month'), getattr(d, 'day'), 0, 0, 0, 0) - datetime.timedelta(days=1)
    FechaInicio= FechaFinal- datetime.timedelta(days=7) # day from the week before
    date_list = [FechaInicio + datetime.timedelta(days=x) for x in range(0, 8)]
    date_list4graphs = [date_list[t].strftime("%d/%m/%Y") for t in range(len(date_list))]

    ###################### 2. OBTENCION DE LOS DATOS DE LOS ARCHIVOS JSON #########################
    data_zones,ObjectID,name,ST_ID = GetInfoJSONzones('static/subwebs/uploads/zonesData.geojson')
    Qmin_globalDF = pd.DataFrame( [], index=date_list)
    Qmedio_globalDF = pd.DataFrame( [], index=date_list) # para poder calcular sumatorio de los caudales de toda network
    Fuga_globalDF = pd.DataFrame( [], index=date_list)

    ###################### 3. CALCULOS DE QMIN, QMEDIO PARA CADA SECTOR Y SUBSECTOR ###############
    dfRaport = pd.DataFrame({'Sector':[],'Q medio':[],'Q min': [], 'Q fuga': [], 'Rendimiento': []})

    for i in range(len(name)): # 87 ---- network Norte
   

        try:
            start2 = timeit.default_timer() # para calcular el tiempo de los caculos
            df = zonesQmedio(ST_ID[i],FechaInicio,FechaFinal)['Total']
            stop2 = timeit.default_timer()
            seconds = stop2 - start2 
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            print name[i], " CALCULATION TIME: %d:%02d:%02d" % (h, m, s)

            medio = [round(df.iat[jj],2) for jj in range(len(df))]
        except Exception as e:
            medio = [0.01 for jj in range(len(date_list))]
       
        Qmedio_globalDF[ST_ID[i]] = medio

    ###################### 3B. CALCULOS DE  QMIN 
        try:   
            start3 = timeit.default_timer() # para calcular el tiempo de los caculos
            minimumTotal = zonesQmin(ST_ID[i],FechaInicio,FechaFinal,date_list)[ST_ID[i]] # do df
            stop3 = timeit.default_timer()
            seconds = stop3 - start3 
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            print name[i], " CALCULATION TIME: %d:%02d:%02d" % (h, m, s)
            minimum = [round(minimumTotal.iat[kk],2) for kk in range(len(minimumTotal))] #zamiana df into lista

        except Exception as e:
            PrintException()
            try:    
                Q_zastepcze = GetUARL(cursor,'typef',ST_ID[i])
                minimum = [Q_zastepcze for ll in range(len(date_list))] # por defecto cogemos 0.01
                minimumTotal = pd.DataFrame({'NO DATA' : pd.Series([Q_zastepcze for xx in range(len(date_list))], index=date_list)})
            except Exception as e:
                PrintException()
                minimumTotal = pd.DataFrame({'NO DATA' : pd.Series([0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01], index=date_list)})
                minimum = [0.01 for ll in range(len(minimumTotal))] # por defecto cogemos 0.01

        Qmin_globalDF = pd.concat([Qmin_globalDF, minimumTotal], axis=1) # dolaczenie pod bazy danych do globalnej bazy dabych
        QminRef = (min(minimumTotal)) # dolaczam wartosc minimalna z Qminimum z ostatniego tygodnia

        try:
            ConsumoNocturno, ConsumoDiario = GetConsumptionSector(ST_ID[i],cursor,date_list)
            try:
                uarl = GetUARL(cursor,'ZP',ST_ID[i]) # si el subsector == sector
            except:
                uarl = GetUARLzones(cursor,ST_ID[i]) # si el sector tiene mas que un subsector
            
            UARL = [uarl for kk in range(len(minimum))]
            Fuga = [round(x - y - z, 2) for x, y, z in zip(minimum, ConsumoNocturno, UARL)]
            Fuga = [0 if x < 0 else x for x in Fuga]

        except Exception as e:
            PrintException()

        ###################### 3C. CALCULOS DE RATIOS PARA zones
        medio = [0.001 if nn == 0 else nn for nn in medio] # para evitar division por 0
        rendimiento =[round( (medio[mm]-Fuga[mm])/medio[mm]*100 ,2) for mm in range(len(medio))]
        rendimiento = [0 if mm < 0 else mm for mm in rendimiento] # para quitar rendimiento menos que 0 

        Fuga_globalDF[ST_ID[i]] = Fuga
        try:
            CreateAwsomePlot(name[i],date_list4graphs,medio,minimum,rendimiento,ObjectID[i],Fuga)
        except:
            pass # p.e. hay un row nulo....
        try:
            ratio2 = (mean(medio)-mean(Fuga))/mean(medio)*100
        except:
            PrintException()
            ratio2 = 9999.99
            
        data_zones['features'][i]['properties']['Ratio'] = str(round(ratio2,2))
        dfRaport.loc[i] = [name[i],mean(medio),mean(minimum),mean(Fuga), ratio2]


    #subzones
    Qmin_globalDF = Qmin_globalDF.fillna(0) # replace all the NaN values with Zero's in a column of a pandas dataframe
    Qmedio_globalDF[Qmedio_globalDF < 0] = 0 # replace negative numbers in Pandas Data Frame by zero

    # network GLOBAL
    Qmedio_globalDF['Total'] = Qmedio_globalDF.sum(axis=1)
    Qmin_globalDF['Total'] = Qmin_globalDF.sum(axis=1)
    MedioGlobal = [Qmedio_globalDF['Total'].iat[kk] for kk in range(len(Qmedio_globalDF['Total']))]
    Fuga_globalDF['Total'] = Fuga_globalDF.sum(axis=1)
    FugaGlobal= [Fuga_globalDF['Total'].iat[kk] for kk in range(len(Fuga_globalDF['Total']))]
    MinGlobal = [Qmin_globalDF['Total'].iat[kk] for kk in range(len(Qmin_globalDF['Total']))]
    MinGlobal = [round(MinGlobal[jj],3) for jj in range(len(MinGlobal))]
    rendimientoGlobal =[(MedioGlobal[mm]-FugaGlobal[mm])/MedioGlobal[mm]*100 for mm in range(len(MedioGlobal))]

    rendimientoGlobal = [0 if x < 0 else x for x in rendimientoGlobal]
    rendimientoGlobal = [round(rendimientoGlobal[i],3) for i in range(len(rendimientoGlobal))]

    # replace all the NaN values with 100's in a column of a pandas dataframe
    for iii in range(len(rendimientoGlobal)):
        if np.isnan(rendimientoGlobal[iii]) == True:
            rendimientoGlobal[iii] = 100.0

    CreateAwsomePlot('network Global',date_list4graphs,MedioGlobal,MinGlobal,rendimientoGlobal,'global',FugaGlobal)
    
    #estimacion anual
    medio_anual = round(mean(MedioGlobal)*365/24,2)
    fuga_anual =  round(mean(FugaGlobal)*365/24,2)
    CreateAwsomePlotAnual(medio_anual,fuga_anual)
    

    try: 
        with open('static/subwebs/uploads/zonesData.geojson', 'w') as f:
            f.write(json.dumps(data_zones))
    except Exception as e:
        pass

    createReportzones(dfRaport)

    JSONtoJS('zonesData')

        
    cursor.close() #close connection with database MDB
    del cursor
    
    stop = timeit.default_timer()
    seconds = stop - start 

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    print "CALCULATION TIME: %d:%02d:%02d" % (h, m, s)
    #############################################################################
    return

def Sortowanie(ID,Nombres):
    df = pd.DataFrame( Nombres, index=ID)
    df = df.sort_values(0,ascending=True)
    Nombres = [df.iloc[:,0].iat[jj] for jj in range(len(df))]
    ID = df.index.values
    lista = zip(ID, Nombres)
    return(lista)

def GetAllzones():
    cursor = MDB() 
    sentenciasql = ("SELECT * FROM zonapresion WHERE (((zonapresion.[Tipo])='ZP')) ORDER BY zonapresion.Nombre;")
    cursor.execute(sentenciasql)
    row = cursor.fetchall()
    Nombres = [i[1] for i in row] #Nombre,idzh
    idzh = [i[2] for i in row] #Nombre,idzh
    zones= zones = Sortowanie(idzh,Nombres)
    return zones
    
def GetAllsubzones():
    cursor = MDB() # r'update\database.mdb'
    sentenciasql = ("SELECT * FROM zonapresion WHERE type=typef")
    cursor.execute(sentenciasql)
    row = cursor.fetchall()
    ID = [i[0] for i in row]
    Nombres = [i[1] for i in row]
    subzones = Sortowanie(ID,Nombres)
    return(subzones)
       
###################### 2. OBTENCION DE LOS DATOS DEL ARCHIVO JSON #########################
def GetInfoJSON(path):
    with open('static/subwebs/uploads/subzonesData.geojson') as f:  
        
        data_subzones = json.load(f)
        SSobjectID,SSname,SST_ID = [],[],[]

    for feature in data_subzones['features']:
        SSobjectID.append(feature['properties']['OBJECTID'])
        SST_ID.append(feature['properties']['SST_ID'])
        SSname.append(feature['properties']['SST_NOMBRE'])
    
    return(data_subzones,SSobjectID,SSname,SST_ID)

def ReportPrepare(contadores,minimumTotal,uarl):
    
    if len(contadores) < 2:
        senal = GetSenal(contadores,MDB())[0]
        senal= str(senal[0])
    else:
        senal ='balance'

    minimum = [round(minimumTotal.iat[_,0],2) for _ in range(len(minimumTotal))]

    if minimum[-1] == 0.01:
        ratio = 9999.99
    elif minimum[-1] < 0.5:
        ratio = 0.0
    elif minimum[-1]== uarl:
        ratio = 9999.99
    elif all(x==minimum[0] for x in minimum) is True: # si todos valores son iguales ( son de UARL..... pues no son verdaderos!)
        ratio = 9999.99
    else:
        ratio = round(minimum[-1]/np.mean(minimum),2)
    return senal,minimum,ratio

def funcion_global_subzones():
    
    ###################### 1. ESTABLECER LAS FECHAS DE CALCULO (LA ULTIMA SEMANA) #################
    d = datetime.datetime.now()    
    savefecha(1,d) # guarda la fecha to JSON file para demonstrarla en el menu INICIO (flask)
    FechaFinal = datetime.datetime(getattr(d,'year'), getattr(d,'month'), getattr(d, 'day'), 0, 0, 0, 0) 
    FechaInicio= FechaFinal- datetime.timedelta(days=7) # day from the week before
    date_list = [FechaInicio + datetime.timedelta(days=x) for x in range(0, 8)]
    date_list4graphs = [date_list[t].strftime("%d/%m/%Y") for t in range(len(date_list))]
    dfRaport = pd.DataFrame({'Nombre del subsector':[],'Señal':[],'Consumo':[], 'Qmin': [],'Ratio2': [], 'Ratio': []})
    data_subzones,SSobjectID,SSname,SST_ID = GetInfoJSON('static/subwebs/uploads/subzonesData.geojson')
    SS_globalDF = pd.DataFrame( [], index=date_list)
    cursor =MDB() # conexión a la base de datos database.mdb

    ###################### 1. ESTABLECER EL CAUDAL MINIMO DE LA ULTIMA SEMANA PARA CADA SUBSECTOR #################

    for i in range(len(SST_ID)): 
    #for i in range(5): 
        try:

            minimumTotal = zonesQmin(SST_ID[i],FechaInicio,FechaFinal,date_list) 
            minimumTotal = minimumTotal.fillna(0.001) # only for df, cambio 'nan' ---> 0
            SS_globalDF = pd.concat([SS_globalDF, minimumTotal], axis=1) # dolaczenie pod bazy danych do globalnej bazy dabych
            
            contadores = GetContadoresAndSignos(SST_ID[i],cursor)[0] # contadory do raportu

            ConsumoNocturno, ConsumoDiario = GetConsumptionAll(cursor,SST_ID[i],date_list)
            ConsumoNocturno =  [0 if y==None else y for y in ConsumoNocturno] 
            uarl = round(GetUARL(cursor,'typef',SST_ID[i]),2)
            senal, minimum, ratio = ReportPrepare(contadores,minimumTotal,uarl)
            UARL = [uarl for kk in range(len(minimum))]
            
            longitud = GetLongitudRed(SST_ID[i])
            ratio2 = round(minimum[-1]*24 / longitud,2)
            dfRaport.loc[i] = [SSname[i],senal, ConsumoNocturno[-1],minimum[-1],ratio2, ratio]
            
            Fuga = [round(x - y - z,2) for x, y, z in zip(minimum, ConsumoNocturno, UARL)] #~calculo de la fuga
            Fuga = [0 if x < 0 else x for x in Fuga] # eliminacion valores menos que 0 
            ConsumoNocturno = [round(ConsumoNocturno[rr],2) for rr in range(len(ConsumoNocturno))]
            
            CreateAwsomePlotSS(SSname[i], date_list4graphs, minimum, SSobjectID[i],ConsumoNocturno, Fuga) # creacion del grafico de la última semana

        except Exception as e:
            #PrintException()
            ratio=9999.99
            dfRaport.loc[i] = [SSname[i],'No INFO',9999.99,9999.99, 9999.99,9999.99]

        data_subzones['features'][i]['properties']['Ratio'] = str(ratio) 
   
        
    with open('static/subwebs/uploads/subzonesData.geojson', 'w') as f:#actualizacja plikow JSON
        f.write(json.dumps(data_subzones))

    JSONtoJS('subzonesData') 

    createReport(dfRaport)

        
    cursor.close()   # shut down connection with database.mbb
    del cursor

    return

def getDates():
    with open('static/fechas.json') as data_file:    
        data = json.load(data_file)
        fecha= data["fechas"][0]["fecha"]
        fechaSS = data["fechas"][1]["fecha"]
    return fecha,fechaSS

def AppWEB():
    #############################################################################
    app = Flask(__name__)

    app.config.update(
        TEMPLATES_AUTO_RELOAD=True,
        SECRET_KEY='********************************'
    )


    @app.route('/')
    def home():
  
        fecha,fechaSS = getDates()
        return render_template('main.html',fecha=fecha,fechaSS=fechaSS)
        
    @app.route('/informe/')
    def informe():
        try:
            return app.send_static_file('informe.pdf')
        except Exception as e:
            return str(e)
            
            
    @app.route('/informe-zones/')
    def informe_zones():
        try:
            return app.send_static_file('informe_zones.pdf')
        except Exception as e:
            return str(e)
        
    @app.route('/calculos-todo/')
    def calculos_todo():
        funcion_global()
        return render_template('main.html')
        
    @app.route('/calculos/')
    def calculos():
        funcion_global_subzones()
        return render_template('subzones.html')

    @app.route('/zones/')
    def zones():
        return render_template('zones.html')
        
    @app.route('/subzones/')
    def subzones():
        return render_template('subzones.html')

    @app.route('/estado/')
    def estado():
        return render_template('estado.html')
        
    @app.route('/network/')
    def network():
        return render_template('network.html')

    @app.route('/sector/')
    def sector():
        zones_info = GetAllzones()
        return render_template('sector.html',zones_info=zones_info)
        
    @app.route('/subsector/')
    def subsector():
        subzones_info = GetAllsubzones()
        return render_template('subsector.html',subzones_info=subzones_info)
        
    @app.route('/network-resultado/',methods=['GET','POST'])
    def replay_network():
        
        try:
            if request.method == 'POST':

                FechaInicio = request.form['fecha1']
                FechaFinal = request.form['fecha2']
                
                idzh = 10019
                
                FechaInicio = parser.parse(FechaInicio)
                FechaFinal = parser.parse(FechaFinal) # zmiana datetime na string

                date_list = [FechaInicio + datetime.timedelta(days=x) for x in range((FechaFinal - FechaInicio).days +1 )]
                date_list4graphs = [date_list[t].strftime("%d/%m/%Y") for t in range(len(date_list))]
           
                df = zonesQmedio(idzh,FechaInicio,FechaFinal)['Total']
                medio = [df.iat[jj] for jj in range(len(df))]
                
                minimumTotal = zonesQmin(idzh,FechaInicio,FechaFinal,date_list)
                minimumTotal = minimumTotal.fillna(0.001) # replace all the NaN values with 0.0001's in a column of a pandas dataframe
                dfMIN = minimumTotal.sum(axis=1)
                QminRef = (min(dfMIN)) # dolaczam wartosc minimalna z Qminimum z ostatniego tygodnia
                minimum = [dfMIN.iat[kk] for kk in range(len(dfMIN))]
                rendimiento =[(medio[mm]-minimum[mm])/medio[mm]*100 for mm in range(len(medio))]
                
                medio = [round(medio[i],3) for i in range(len(medio))]
                minimum = [round(minimum[i],3) for i in range(len(minimum))]
                rendimiento = [round(rendimiento[i],3) for i in range(len(rendimiento))]
        except Exception as e:
            #PrintException()
            pass

        return render_template('network-resultado.html',idzh = idzh, date_list4graphs=date_list4graphs,medio=medio,minimum=minimum,rendimiento=rendimiento)

    @app.route('/sector-resultado/',methods=['GET','POST'])
    def replay_sector():
        zones_info = GetAllzones()
        cursor =MDB()

        try:
            if request.method == 'POST':

                FechaInicio = request.form['fecha1']
                FechaFinal = request.form['fecha2']
                
                idzh = request.form['lista']
                idzh = float(idzh) # p.e. el puntal tiene idzh en el formato str...
                nombre = GetNombreZona(idzh, MDB()) 
                FechaInicio = parser.parse(FechaInicio)
                FechaFinal = parser.parse(FechaFinal) # zmiana datetime na string
                date_list = [FechaInicio + datetime.timedelta(days=x) for x in range((FechaFinal - FechaInicio).days +1 )]
                date_list4graphs = [date_list[t].strftime("%d/%m/%Y") for t in range(len(date_list))]
          
                valores = zonesQmedio(idzh,FechaInicio,FechaFinal)['Total']
    
                medio = [valores.iat[jj] for jj in range(len(valores))]
       
                minimumTotal = zonesQmin(idzh,FechaInicio,FechaFinal,date_list)
                minimumTotal = minimumTotal.fillna(0.001) # replace all the NaN values with 0.0001's in a column of a pandas dataframe
                dfMIN = minimumTotal.sum(axis=1)
                minimum = [dfMIN.iat[kk] for kk in range(len(dfMIN))]

                try:
                    ConsumoNocturno, ConsumoDiario = GetConsumptionSector(idzh,cursor,date_list)
                    try:
                        uarl = GetUARL(cursor,'ZP',idzh) # si el subsector == sector
                    except:                  
                        uarl = GetUARLzones(cursor,idzh) # si el sector tiene mas que un subsector

                    UARL = [uarl for kk in range(len(minimum))]
       
                    Fuga = [round(x - y - z, 2) for x, y, z in zip(minimum, ConsumoNocturno, UARL)]
                    Fuga = [0 if x < 0 else x for x in Fuga]
 
                    rendimiento =[(medio[mm]-Fuga[mm])/medio[mm]*100 for mm in range(len(medio))]
          
                except Exception as e:
                    rendimiento =[(medio[mm]-minimum[mm])/medio[mm]*100 for mm in range(len(medio))]
                
                rendimiento = [round(rendimiento[i],3) for i in range(len(rendimiento))]
                minimum = [round(minimum[i],3) for i in range(len(minimum))]
                medio = [round(medio[i],3) for i in range(len(medio))]
                
             
        except Exception as e:
            pass

        return render_template('sector-resultado.html',idzh = idzh, date_list4graphs=date_list4graphs,medio=medio,minimum=minimum,rendimiento=rendimiento,nombre =nombre,zones_info=zones_info,Fuga =Fuga)

    @app.route('/subsector-resultado/',methods=['GET','POST'])
    def replay_subsector():

        subzones_info = GetAllsubzones()
        cursor = MDB()

        if request.method == 'POST':
           
            FechaInicio = request.form['fecha1']
            FechaFinal = request.form['fecha2']
       
            idzh = request.form['lista']
            idzh = float(idzh)
            nombre = GetNombreZona(idzh, cursor)

            FechaInicio = parser.parse(FechaInicio)
            FechaFinal = parser.parse(FechaFinal)

            date_list = [FechaInicio + datetime.timedelta(days=x) for x in range((FechaFinal - FechaInicio).days +1 )]
            date_list4graphs = [date_list[t].strftime("%d/%m/%Y") for t in range(len(date_list))]

            df = zonesQmin(idzh,FechaInicio,FechaFinal,date_list)[str(int(idzh))]

            df = df.fillna(0.001) # replace all the NaN values with 0.0001's in a column of a pandas dataframe
     
            minimum = [round(df.iat[jj],2) for jj in range(len(df))]
        
            ConsumoNocturno, ConsumoDiario = GetConsumptionAll(cursor,idzh,date_list)

            UARL = [GetUARL(cursor,'typef',idzh) for kk in range(len(minimum))]
      
            Fuga = [round(x - y - z,2) for x, y, z in zip(minimum, ConsumoNocturno, UARL)]

   
            ConsumoNocturno = [ round(ConsumoNocturno[_],2) for _ in range(len(ConsumoNocturno))]
     
            Fuga = [0 if x < 0 else x for x in Fuga]

            return render_template('subsector-resultado.html',idzh = idzh, date_list4graphs=date_list4graphs,minimum=minimum,nombre =nombre,subzones_info=subzones_info,ConsumoNocturno=ConsumoNocturno,Fuga=Fuga)
      
    @app.route('/select-file/')
    def SelectFile():
        return render_template('select-file.html')
        
    # Route that will process the file upload
    @app.route('/upload', methods=['POST'])
    def upload():
        file = request.files['file'] # Get the name of the uploaded file
        if file and allowed_file(file.filename): # Check if the file is one of the allowed types/extensions
            filename = secure_filename(file.filename) # Make the filename safe, remove unsupported chars
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # Move the file form the temporal folder to the upload folder I setup
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
            return render_template('main.html')

    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route('/shutdown/', methods=['POST'])
    def shutdown():
        shutdown_server()
        return 'Server shutting down...'
        

    if __name__ == '__main__':
        port = 5000 + random.randint(0, 999)
        url = "http://127.0.0.1:{0}".format(port)
        #webbrowser.get("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s").open(url)
        threading.Timer(1.25, lambda: webbrowser.open(url) ).start()
        #threading.Timer(1.25, lambda: webbrowser.get("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s").open(url)).start()
        app.run(port=port, debug=False)
    return

########################

import csv,datetime,pyodbc,time,timeit,itertools


def MDB_secret():
    ACCESS_DATABASE_FILE = '******' # acesso al base de datos padron
    ODBC_CONN_STR = 'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;' % ACCESS_DATABASE_FILE
    cnxn = pyodbc.connect(ODBC_CONN_STR)
    cursor = cnxn.cursor()
    return cursor

def ContadoresSubsector(SST_ID,cursor): 
    sentenciasql = ("SELECT ncmdm FROM msec WHERE sstid=?")
    cursor.execute(sentenciasql,(SST_ID))
    row = cursor.fetchall()
    contadores = [[i][0][0] for i in row]
    return contadores

def SSTid(cursor): 
    sentenciasql = ("SELECT sstid FROM msec")
    cursor.execute(sentenciasql)
    row = cursor.fetchall()
    row =  [[i][0][0] for i in row]
    lista_SST = filter(None, set(row))
    return lista_SST

def Diccionario(cursor):
   
    sentenciasql = ("SELECT * FROM dmdm")
    cursor.execute(sentenciasql)
    row = cursor.fetchall()
    contadores = [ row[i][0] for i in range(len(row))]
    contadoresMDM =[ row[i][1] for i in range(len(row))]
    
    return contadores,contadoresMDM

def ActulizacionMDM(d,path):
    data =d.strftime("%Y-%m-%d")
    cursor = MDB_secret()
    contadores,contadoresMDM = Diccionario(cursor)
    lista_SST = SSTid(cursor)

    df = pd.read_csv(path,sep=';',na_values=[''],header=None,dayfirst=True, date_parser=[0],usecols =[2,4,5]) # cambio del formato de CSV
    df = df[df[2].isin(contadoresMDM)] # cogemos solo contadores desde el archivo diccionario columna A

    gb = df.groupby(2)   
    ListaGrup = [gb.get_group(x) for x in gb.groups]

    nombres, consumos_nocturnos,consumos_diarios,ContSinData = [],[],[],[]

    start = timeit.default_timer()
    for j in range(len(ListaGrup)):

        contador = ListaGrup[j] # bierzemy dane dla contadoru j
        nombres.append(contador[2].iat[0])
        contador.sort_values(by=[4], ascending=[False])
        caudal = [ contador[5].iat[i] - contador[5].iat[i+1] for i in range(len(contador)-1)]
        contador = contador[:-1] 

        caudal = pd.Series(caudal)
        contador = contador.assign(caudal=caudal.values)

        hours = pd.Series([ pd.to_datetime(contador[4].iat[i]).round('60min').hour for i in range(len(contador))]) #  godziny zaokraglamy do pelnych godzin
        contador = contador.assign(hours=hours.values) 
		
        mask = (contador['hours'] > 1) & (contador['hours'] <5) # bierzemy wartosci dla godzin 2,3,4,5

        try:
            consumos_nocturnos.append((min(contador['caudal'].loc[mask]))/1000.00) # bierzemy tylko minimum z wybranych godzin
        except Exception as e:
            consumos_nocturnos.append(0)  # no hay datos entr 2 y 5
            ContSinData.append(nombres[j]) #dodajemy do listy contadory ktore nie maja wartosci #0:02:40
            
    stop = timeit.default_timer()
    seconds = stop - start 

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print "CALCULATION TIME: %d:%02d:%02d" % (h, m, s) 


    Fechas = [d.strftime("%Y-%m-%d") for i in range(len(nombres))]
    result = pd.DataFrame( {'Contador':nombres,'Fecha': Fechas, 'Consumo Nocturno': consumos_nocturnos})
   

    #########################################################################################################################
    start = timeit.default_timer()
    new_coursor =MDB()
    for i in range(len(lista_SST)):

        SST_ID = lista_SST[i] #id del subsector
        contadores = ContadoresSubsector(SST_ID,cursor) # sus contadores segun la tabla NUMERO CONTADOR MDM
        miniDF = result.loc[result['Contador'].isin(contadores)]['Consumo Nocturno']
        valores = [miniDF.iat[jj] for jj in range(len(miniDF))]
        valores = [0 if jj < 0 else jj for jj in valores] # cambio de los valores menores que 0 a 0
        ConsumoNocturno= sum(valores) # suma de los consumos nocturnos
        #ConsumoNocturno = round(ConsumoNocturno,2) 

        new_coursor.execute("insert into [Consumos subzones](Id,Dia,[Consumo m\xednimo]) values (?,?,?)", SST_ID, data,ConsumoNocturno)
        new_coursor.commit()




    stop = timeit.default_timer()
    seconds = stop - start 

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print "CALCULATION TIME: %d:%02d:%02d" % (h, m, s)
    #########################################################################################################################
    return

###############################
import Tkinter 
import pandas as pd
import ttk, tkMessageBox, tkFileDialog,tkSimpleDialog

root = Tkinter.Tk()
root.wm_title("Panel ANR")
root.resizable(width=False, height=False)
# Names of the functions 
options = { 'subzones':'Calcula los subzones de la ultima semana', 
           'zones':'Calcula los zones de la ultima semana', 
           'todo':'Calcula los zones y los subzones de la ultima semana', 
           'MDM': 'Introduzca datos del consumo dc MDM (*csv)',
           'webapp':'VISUALIZACIÓN DE LOS RESULTADOS'}

# State variables
option = Tkinter.StringVar()
sentmsg = Tkinter.StringVar()
statusmsg = Tkinter.StringVar()

# Called when the user double clicks an item in the listbox, presses
# the "Send option" button, or presses the Return key.  In case the selected
# item is scrolled out of view, make sure it is visible.
#
# Figure out which country is selected, which option is selected with the 
# radiobuttons, "send the option", and provide feedback that it was sent.
def sendoption(*args):

    if  options[option.get()] =='Calcula los subzones de la ultima semana':
        start = timeit.default_timer() # para calcular el tiempo de los caculos
        funcion_global_subzones()
        stop = timeit.default_timer()
        seconds = stop - start 
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        tkMessageBox.showinfo("INFO", "Se ha terminado los calculos. Tiempo de caculos: %d:%02d:%02d" % (h, m, s) )
        
    elif  options[option.get()] =='Calcula los zones de la ultima semana':
        start = timeit.default_timer() # para calcular el tiempo de los caculos
        funcion_global()
        stop = timeit.default_timer()
        seconds = stop - start 
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        tkMessageBox.showinfo("INFO", "Se ha terminado los calculos. Tiempo de caculos: %d:%02d:%02d" % (h, m, s) )
        
    elif  options[option.get()] =='Introduzca datos del consumo dc MDM (*csv)':
        path = tkFileDialog.askopenfilename()
        fecha = tkSimpleDialog.askstring('Fecha del calculo', 'Introduzca la fecha del calculo en formato DD/MM/YYYY')
        try:
            d = pd.to_datetime(fecha,dayfirst = True)
        except Exception as e:
            tkMessageBox.showinfo("ERROR",(e.message, e.args))
            d= 'Error'
        try:
            ActulizacionMDM(d,path)
            tkMessageBox.showinfo("INFO", "El proceso se ha terminado corectamente")
        except Exception as e:
            tkMessageBox.showinfo("ERROR",(e.message, e.args))
            #PrintException()

    elif options[option.get()]=='VISUALIZACIÓN DE LOS RESULTADOS':
        AppWEB()



# Create and grid the outer content frame
c = ttk.Frame(root, padding=(5, 5, 12, 0))
c.grid(column=0, row=0, sticky=(Tkinter.N,Tkinter.W,Tkinter.E,Tkinter.S))
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0,weight=1)

# Create the different widgets; note the variables that many
# of them are bound to, as well as the button callback.
# Note we're using the StringVar() 'cnames', constructed from 'countrynames'

lbl = ttk.Label(c, text="SELECIONE UNA OPCIÓN:", font=("Helvetica", 12), justify=Tkinter.LEFT,background='white')
g1 = ttk.Radiobutton(c, text=options['webapp'], variable=option, value='webapp')
g2 = ttk.Radiobutton(c, text=options['zones'], variable=option, value='zones')
g3 = ttk.Radiobutton(c, text=options['subzones'], variable=option, value='subzones')
g4 = ttk.Radiobutton(c, text=options['MDM'], variable=option, value='MDM')


send = ttk.Button(c, text='EJECUTA', command=sendoption, default='active')
sentlbl = ttk.Label(c, textvariable=sentmsg, anchor='center')
status = ttk.Label(c, textvariable=statusmsg, anchor=Tkinter.W)

# Grid all the widgets
lbl.grid(column=1, row=0, padx=20, pady=20)
g1.grid(column=1, row=1, sticky=Tkinter.W, padx=20, pady=20)
g2.grid(column=1, row=2, sticky=Tkinter.W, padx=20)
g3.grid(column=1, row=3, sticky=Tkinter.W, padx=20)
g4.grid(column=1, row=4, sticky=Tkinter.W, padx=20)


send.grid(column=2, row=4, sticky=Tkinter.E)
sentlbl.grid(column=1, row=5, columnspan=2, sticky=Tkinter.N, pady=5, padx=5)
status.grid(column=0, row=6, columnspan=2, sticky=(Tkinter.W,Tkinter.E))
c.grid_columnconfigure(0, weight=1)
c.grid_rowconfigure(5, weight=1)


sentmsg.set('')
statusmsg.set('')

root.mainloop()
