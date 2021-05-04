###########################################################################
# Librairies

import os
import FichiersFSMS as fs
os.chdir(r'C:\Users\lebce\OneDrive\Documents\DataForGood')
print(os.getcwd())

import pandas as pd
#import unicodedata
import geopandas as gpd                 
import rasterio
from rasterio.plot import show
import numpy as np
import scipy.special
import gdal                            
import matplotlib.cm
import folium                           
from folium import plugins
from math import sqrt

###########################################################################
# Import des fichiers : Crop Mask + Hist Yield

monRep=r'C:\Users\lebce\OneDrive\Documents\DataForGood\0 - Data\Data for Good (saison 9) - projet GeoWatch Labs\GeoWatch Labs Agricultural Maps\Crop masks'
liCropMask = []
liCropMask_np = []
for path, subdirs, files in os.walk(monRep):
    for name in files:
        #print(os.path.join(path, name))
        fileExtension=name[len(name)-4:len(name)]
        if fileExtension==".tif" : 
            #print(os.path.join(path, name))
            rast_rend = rasterio.open(os.path.join(path, name))
            annee=path[path.find('20'):path.find('20')+4]
            temp=name[name.find('_')+1:len(name)]
            temp=temp[temp.find('_')+1:len(temp)]
            prod=temp[temp.find('_')+1:len(temp)-17]
            temp=name[name.find('_')+1:len(name)]
            temp=temp[temp.find('_')+1:len(temp)]
            zone=name[0:len(name)-len(temp)-1]
            liCropMask.append([annee,prod,path,name,zone,rast_rend,rast_rend.height,rast_rend.width])
            liCropMask_np.append([rast_rend.read(1)])



monRep=r'C:\Users\lebce\OneDrive\Documents\DataForGood\0 - Data\Data for Good (saison 9) - projet GeoWatch Labs\GeoWatch Labs Agricultural Maps\Historical Yields'
liHistYield = []
liHistYield_np = []
for path, subdirs, files in os.walk(monRep):
    for name in files:
        #print(os.path.join(path, name))
        fileExtension=name[len(name)-4:len(name)]
        if fileExtension==".tif" : 
            #print(os.path.join(path, name))
            rast_rend = rasterio.open(os.path.join(path, name))
            annee=path[path.find('20'):path.find('20')+4]
            prod=path[len(path)-7:len(path)]
            if prod=="\\cowpea": prod="cowpea"
            if prod=="s\maize": prod="maize"
            if prod=="\millet": prod="millet"
            if prod=="oundnut": prod="groundnut"
            temp=name[name.find('_')+1:len(name)]
            temp=temp[temp.find('_')+1:len(temp)]
            zone=name[0:len(name)-len(temp)-1]
            liHistYield.append([annee,prod,path,name,zone,rast_rend,rast_rend.height,rast_rend.width])
            liHistYield_np.append([rast_rend.read(1)])

# nettoyage
del monRep ,rast_rend,path, subdirs, files,fileExtension, name, annee, temp,prod,zone


# transformation des cartes en DF / listes utilisées dans la suite du programme
List_drop=['path','rast_rend']
df_HistYield = pd.DataFrame(liHistYield,columns=["annee","prod","path","name","zone","rast_rend","height","width"])
df_HistYield=df_HistYield.drop(List_drop,axis=1)
list_annee_HY=list(df_HistYield['annee'].unique())
list_prod_HY=list(df_HistYield['prod'].unique())
list_name_HY=list(df_HistYield['name'].unique())

df_CropMask = pd.DataFrame(liCropMask,columns=["annee","prod","path","name","zone","rast_rend","height","width"])
df_CropMask=df_CropMask.drop(List_drop,axis=1)
list_annee_CM=list(df_CropMask['annee'].unique())
list_prod_CM=list(df_CropMask['prod'].unique())
list_name_CM=list(df_CropMask['name'].unique())

df_HistYield["CATE"]=df_HistYield["annee"].astype(str)+"_"+df_HistYield["prod"]+"_"+df_HistYield["zone"]
df_CropMask["CATE"]=df_CropMask["annee"].astype(str)+"_"+df_CropMask["prod"]+"_"+df_CropMask["zone"]

del List_drop






###########################################################################
# chargement de la base des ménages

df_analyse=fs.df_analyse.copy()

###########################################################################
# calcul des coordonnées sur toute la base Rendements

# calcul des rendements par annee, prod et zone pour chaque ménage
for i in range(len(liHistYield)) :
    temp=liHistYield[i][0]+"_"+liHistYield[i][1]+"_"+liHistYield[i][4] # annee + prod + zone
    df_analyse["HY_row_"+temp],df_analyse["HY_col_"+temp] = liHistYield[0][5].index(pd.to_numeric(df_analyse["LONGITUDE"], errors='coerce'), 
                              pd.to_numeric(df_analyse["LATITUDE"], errors='coerce'))
    max_row=liHistYield[i][6]
    max_col=liHistYield[i][7]
    df_analyse.loc[df_analyse["HY_row_"+temp]< 0 , ["HY_row_"+temp]]=0
    df_analyse.loc[df_analyse["HY_row_"+temp]> max_row , ["HY_row_"+temp]]=0
    
    df_analyse.loc[df_analyse["HY_col_"+temp]< 0 , ["HY_col_"+temp]]=0
    df_analyse.loc[df_analyse["HY_col_"+temp]> max_col , ["HY_col_"+temp]]=0
    
    #df_analyse["HY_Rend_"+temp]=liHistYield_np[i][0][df_analyse["HY_row_"+temp]][df_analyse["HY_col_"+temp]]
    df_analyse["HY_Rend_"+temp]=liHistYield_np[i][0][309][502]

del max_row, max_col, temp, i

# somme des rendements par annee, prod pour chaque ménage
for an in range(len(list_annee_HY)) :
    for prod in range(len(list_prod_HY)) :
        list = [col for col in df_analyse.columns if col.startswith('HY_Rend_'+str(list_annee_HY[an])+"_"+str(list_prod_HY[prod]))]
        nom=str(list_annee_HY[an])+"_"+str(list_prod_HY[prod])
        df_analyse["HY_Rend_som_"+nom]=df_analyse[list].sum(skipna=True, axis=1)

del an, prod, nom, list

# affichage des résultats
list = [col for col in df_analyse.columns if col.startswith('HY_Rend_som_')]
a=df_analyse[list]

del a, list

# somme des rendements par prod pour chaque ménage en fonction de la date
df_analyse["HY_Rend_tot_cowpea"]=0
df_analyse["HY_Rend_tot_groundnut"]=0
df_analyse["HY_Rend_tot_maize"]=0
df_analyse["HY_Rend_tot_millet"]=0
df_analyse["HY_Rend_tot_sorghum"]=0

for prod in range(len(list_prod_HY)) :
    df_analyse.loc[df_analyse["FICHIER"]=="June-11",'HY_Rend_tot_'+list_prod_HY[prod]]= df_analyse["HY_Rend_som_2010_"+list_prod_HY[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-12",'HY_Rend_tot_'+list_prod_HY[prod]]= df_analyse["HY_Rend_som_2011_"+list_prod_HY[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-13",'HY_Rend_tot_'+list_prod_HY[prod]]= df_analyse["HY_Rend_som_2012_"+list_prod_HY[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-14",'HY_Rend_tot_'+list_prod_HY[prod]]= df_analyse["HY_Rend_som_2013_"+list_prod_HY[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-15",'HY_Rend_tot_'+list_prod_HY[prod]]= df_analyse["HY_Rend_som_2014_"+list_prod_HY[prod]] 

del prod

###########################################################################
# calcul des coordonnées sur toute la base taux de rendement


for i in range(len(liCropMask)) :
    temp=liCropMask[i][0]+"_"+liCropMask[i][1]+"_"+liCropMask[i][4] # annee + prod + zone
    df_analyse["CM_row_"+temp],df_analyse["CM_col_"+temp] = liCropMask[0][5].index(pd.to_numeric(df_analyse["LONGITUDE"], errors='coerce'), 
                              pd.to_numeric(df_analyse["LATITUDE"], errors='coerce'))
    max_row=liCropMask[i][6]
    max_col=liCropMask[i][7]
    df_analyse.loc[df_analyse["CM_row_"+temp]< 0 , ["CM_row_"+temp]]=0
    df_analyse.loc[df_analyse["CM_row_"+temp]> max_row , ["CM_row_"+temp]]=0
    
    df_analyse.loc[df_analyse["CM_col_"+temp]< 0 , ["CM_col_"+temp]]=0
    df_analyse.loc[df_analyse["CM_col_"+temp]> max_col , ["CM_col_"+temp]]=0
    
    #df_analyse["CM_Rend_"+temp]=liCropMask_np[i][0][df_analyse["CM_row_"+temp]][df_analyse["CM_col_"+temp]]
    df_analyse["CM_Rend_"+temp]=liCropMask_np[i][0][309][502]
   
del max_row, max_col, temp, i

# somme des rendements par annee, prod pour chaque ménage
for an in range(len(list_annee_CM)) :
    for prod in range(len(list_prod_CM)) :
        list = [col for col in df_analyse.columns if col.startswith('CM_Rend_'+str(list_annee_CM[an])+"_"+str(list_prod_CM[prod]))]
        nom=str(list_annee_CM[an])+"_"+str(list_prod_CM[prod])
        df_analyse["CM_Rend_som_"+nom]=df_analyse[list].sum(skipna=True, axis=1)

del an, prod, nom, list

# affichage des résultats
list = [col for col in df_analyse.columns if col.startswith('CM_Rend_som_')]
a=df_analyse[list]

del a, list

# somme des rendements par prod pour chaque ménage en fonction de la date
df_analyse["CM_Rend_tot_cowpea"]=0
df_analyse["CM_Rend_tot_groundnut"]=0
df_analyse["CM_Rend_tot_maize"]=0
df_analyse["CM_Rend_tot_millet"]=0
df_analyse["CM_Rend_tot_sorghum"]=0

for prod in range(len(list_prod_CM)) :
    df_analyse.loc[df_analyse["FICHIER"]=="June-11",'CM_Rend_tot_'+list_prod_CM[prod]]= df_analyse["CM_Rend_som_2010_"+list_prod_CM[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-12",'CM_Rend_tot_'+list_prod_CM[prod]]= df_analyse["CM_Rend_som_2011_"+list_prod_CM[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-13",'CM_Rend_tot_'+list_prod_CM[prod]]= df_analyse["CM_Rend_som_2012_"+list_prod_CM[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-14",'CM_Rend_tot_'+list_prod_CM[prod]]= df_analyse["CM_Rend_som_2013_"+list_prod_CM[prod]] 
    df_analyse.loc[df_analyse["FICHIER"]=="June-15",'CM_Rend_tot_'+list_prod_CM[prod]]= df_analyse["CM_Rend_som_2014_"+list_prod_CM[prod]] 

del prod

# affichage des résultats
list = [col for col in df_analyse.columns if col.startswith('CM_Rend_tot_')]
a=df_analyse[list]

del a, list

###########################################################################




