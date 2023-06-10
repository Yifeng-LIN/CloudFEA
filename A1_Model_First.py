import os
import gmsh
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas import read_csv, DataFrame, concat, Series
from mpl_toolkits.mplot3d.art3d import Poly3DCollection





################################################################################################
############################################################################### Function
def ClearSpace(df):
    for c in df.columns:
        for i in range(10):
            df[c] = df[c].astype(str).str.replace(" ","").copy()
    return df





################################################################################################
############################################################################### Parameter
################################################################################################
folder_name = "data_20230510090201_0001"

system      = "Win"  if sys.platform=="win32" else "Linux"
folder_data = "..\\data\\"+folder_name+"\\" if system=="Win" else "../data/"+folder_name + "/"




################################################################################################
############################################################################### Code
################################################################################################

########################################################## Input read
############################# Read from Input
ls_col = ["C"+str(x) for x in np.arange(100)]
df_inp = read_csv(folder_data + "Input.txt", header=None, names=ls_col)
df_inp = df_inp.loc[df_inp["C0"].str[0]!="#"].copy()
df_inp = df_inp.dropna(axis=1, how="all").copy()



########################################################## Df creation
############################# Esize
df_ESize  = df_inp.loc[df_inp["C0"]=="ESIZE"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_ESize.shape[0]>0:
    df_ESize  = ClearSpace(df_ESize)
    df_ESize.columns = ["Command","E_Size"]
df_ESize.to_csv(folder_data + "Input_df_ESize.csv", index=None)



############################# Point
df_P  = df_inp.loc[df_inp["C0"]=="P"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_P.shape[0]>0:
    df_P  = ClearSpace(df_P)
    df_P.columns = ["Command","Pn","GName","X","Y","Z"]
    df_P["Pn"]   = df_P["Pn"].astype(int)
    df_P[["X","Y","Z"]]   = df_P[["X","Y","Z"]].astype(float)
df_P.to_csv(folder_data + "Input_df_Geom_P.csv", index=None)



############################# Line
df_L  = df_inp.loc[df_inp["C0"]=="L"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_L.shape[0]>0:
    df_L  = ClearSpace(df_L)
    df_L.columns = ["Command","Ln","GName","P1","P2"]
    df_L[["Ln","P1","P2"]]   = df_L[["Ln","P1","P2"]].astype(float).astype(int)
df_L.to_csv(folder_data + "Input_df_Geom_L.csv", index=None)



############################# Section Line
df_LSec  = df_inp.loc[df_inp["C0"]=="LSec"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_LSec.shape[0]>0:
    df_LSec  = ClearSpace(df_LSec)
    df_LSec.columns = ["Command","GName","HZ","HY"]
    df_LSec[["HZ","HY"]] = df_LSec[["HZ","HY"]].astype(float)
df_LSec.to_csv(folder_data + "Input_df_Geom_LSec.csv", index=None)



############################# Surface
df_S  = df_inp.loc[df_inp["C0"]=="S"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_S.shape[0]>0:
    df_S  = ClearSpace(df_S)
    Nb_Point  = df_S.shape[1] - 3
    ls_point  = ["P"+str(i+1) for i in range(Nb_Point)]
    df_S.columns = ["Command","Sn","GName"] + ls_point
    df_S[["Sn"] + ls_point]   = df_S[["Sn"] + ls_point].astype(float).astype(int)
df_S.to_csv(folder_data + "Input_df_Geom_S.csv", index=None)



############################# Section Line
df_SSec  = df_inp.loc[df_inp["C0"]=="SSec"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_SSec.shape[0]>0:
    df_SSec  = ClearSpace(df_SSec)
    df_SSec.columns = ["Command","GName","HZ"]
    df_SSec["HZ"]    = df_SSec["HZ"].astype(float)
df_SSec.to_csv(folder_data + "Input_df_Geom_SSec.csv", index=None)



############################# Limite condition
df_LimCo = df_inp.loc[df_inp["C0"]=="LIMCO"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_LimCo.shape[0]>0:
    df_LimCo = ClearSpace(df_LimCo)
    df_LimCo.columns = ["Command","Type","GName"]
df_LimCo.to_csv(folder_data + "Input_df_LimCo.csv", index=None)



############################# Loads
df_Loads = df_inp.loc[df_inp["C0"]=="LOADS"].dropna(axis=1, how="all").reset_index(drop=True).copy()
if df_Loads.shape[0]>0:
    df_Loads = ClearSpace(df_Loads)
    df_Loads.columns = ["Command","LC","Type","Value","GName"]
df_Loads["Value"] = (df_Loads["Value"].astype(float) * 1000).copy()    # KN KPa is used
df_Loads.to_csv(folder_data + "Input_df_Loads.csv", index=None)



############################# Group
df_G = DataFrame()
i    = 0
for GName in df_P["GName"].unique():
    i      += 1
    df_tmp = DataFrame([[GName, "GM"+str(i)]])
    df_G   = concat([df_G, df_tmp]).copy()
for GName in df_L["GName"].unique():
    i      += 1
    df_tmp = DataFrame([[GName, "GM"+str(i)]])
    df_G   = concat([df_G, df_tmp]).copy()
for GName in df_S["GName"].unique():
    i      += 1
    df_tmp = DataFrame([[GName, "GM"+str(i)]])
    df_G   = concat([df_G, df_tmp]).copy()
df_G.columns = ["GName","GNo"]
df_G = df_G.reset_index(drop=True)
df_G.to_csv(folder_data + "Input_df_GNo.csv", index=None)



############################# Delete Track
filename = folder_data + "Output_rs_UseRatio_Track.csv"
if os.path.exists(folder_data + "Output_rs_UseRatio_Track.csv"):
    os.remove(filename)






