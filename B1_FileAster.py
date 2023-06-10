import os
import gmsh
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas import read_csv, DataFrame, concat, Series
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys





################################################################################################
############################################################################### Parameter
################################################################################################
folder_name = "data_20230510090201_0001"

system      = "Win"  if sys.platform=="win32" else "Linux"
folder_data = "..\\data\\"+folder_name+"\\" if system=="Win" else "../data/"+folder_name + "/"
folder_expo = "D:\\calculhub\\autodim_dash\\data\\"+folder_name+"\\" if system=="Win" else "/home/tirazone/calculhub/autodim/data/"+folder_name + "/"





################################################################################################
############################################################################### Code
################################################################################################

############################################################################### Data preparation
############################# Read from Input
df_ESize = read_csv(folder_data + "Input_df_ESize.csv")
df_P     = read_csv(folder_data + "Input_df_Geom_P.csv")
df_LSec  = read_csv(folder_data + "Input_df_Geom_LSec.csv")
df_L     = read_csv(folder_data + "Input_df_Geom_L.csv")
df_SSec  = read_csv(folder_data + "Input_df_Geom_SSec.csv")
df_S     = read_csv(folder_data + "Input_df_Geom_S.csv")
df_LimCo = read_csv(folder_data + "Input_df_LimCo.csv")
df_Loads = read_csv(folder_data + "Input_df_Loads.csv")
df_GNo   = read_csv(folder_data + "Input_df_GNo.csv")
di_LSec  = df_LSec.set_index("GName").to_dict()
di_SSec  = df_SSec.set_index("GName").to_dict()


############################# Esize
Es       = df_ESize["E_Size"].item()


############################# Proprety BC
df_Propr_BC = df_L.loc[df_L["GName"].str[:4].isin(["Beam","Colu"])].copy()
if df_Propr_BC.shape[0]>0:
    df_Propr_BC["EType"] = "POU_D_T"
    df_Propr_BC["Mater"] = "concrete"
    df_Propr_BC["Thick"] = "'RECTANGLE'|'HY';'HZ'|" + \
                        df_Propr_BC["GName"].map(di_LSec["HY"]).astype(str) + ";" +\
                        df_Propr_BC["GName"].map(di_LSec["HZ"]).astype(str)
df_Propr_BC = df_Propr_BC[["GName","EType","Mater","Thick"]].drop_duplicates().reset_index(drop=True).copy()
df_Propr_BC.to_csv(folder_data + "Input_df_Propr_BC.csv", index=None)
    

############################# Proprety SW
df_Propr_SW = df_S.loc[df_S["GName"].str[:4].isin(["Slab","Wall"])].copy()
if df_Propr_SW.shape[0]>0:
    df_Propr_SW["EType"] = "DKT"
    df_Propr_SW["Mater"] = "concrete"
    df_Propr_SW["Thick"] = df_Propr_SW["GName"].map(di_SSec["HZ"]).astype(str)
df_Propr_SW = df_Propr_SW[["GName","EType","Mater","Thick"]].drop_duplicates().reset_index(drop=True).copy()
df_Propr_SW.to_csv(folder_data + "Input_df_Propr_SW.csv", index=None)




############################################################################### .msh for gmsh model
############################# Initialize
gmsh.initialize()


############################# Point
if df_P.shape[0] != 0:
    for i in df_P.index:
        Pn = int(df_P.loc[i, "Pn"])
        X  = float(df_P.loc[i, "X"])
        Y  = float(df_P.loc[i, "Y"])
        Z  = float(df_P.loc[i, "Z"])
        gmsh.model.geo.add_point(X, Y, Z, Es, Pn)


############################# Line
if df_L.shape[0] != 0:
    for i in df_L.index:
        Ln = int(df_L.loc[i, "Ln"])
        P1 = int(df_L.loc[i, "P1"])
        P2 = int(df_L.loc[i, "P2"])
        gmsh.model.geo.add_line(P1, P2, Ln)


############################# Surface
Ln3 = 0
if df_S.shape[0] != 0:
    for i in df_S.index:
        
        ######### Get list of points in surface
        Sn    = int(df_S.loc[i, "Sn"])
        ls_P1 = df_S.drop(columns=["Command","Sn","GName"]).loc[i].dropna().astype(int).tolist()
        if -999 in ls_P1: ls_P1.remove(-999)
        ls_P2 = ls_P1 + [ls_P1[0]]
        
        ######### Get list of lines in surface
        ls_L  = []
        for j in range(len(ls_P2)-1):
            P1 = int(ls_P2[j])
            P2 = int(ls_P2[j+1])
            
            ######### Judgement of case
            ### Case 1
            if df_L.shape[0] == 0:
                Statue = "No self defined line"
            ### With existed line
            else:
                df_L2 = df_L.copy()   #########################
                # Case 2
                if ((df_L2["P1"]==P1) & (df_L2["P2"]==P2)).any():
                    Statue = "Self defined line used - case 2"
                # Case 3
                elif ((df_L2["P1"]==P2) & (df_L2["P2"]==P1)).any():
                    Statue = "Self defined line used - case 3"
                # Case 4
                else:
                    Statue = "Self defined line not used"
                    
            ######### Set ls_L with case
            if (Statue == "No self defined line") or (Statue == "Self defined line not used"):
                Ln3  += 1
                gmsh.model.geo.add_line(P1, P2, Ln3)
                df_L   = concat([df_L, DataFrame([[Ln3,P1,P2]], columns=["Ln","P1","P2"])]).reset_index(drop=True)
                ls_L.append(Ln3)

            elif Statue == "Self defined line used - case 2":
                Ln2  = df_L2.loc[((df_L2["P1"]==P1) & (df_L2["P2"]==P2)), "Ln"].item()
                ls_L.append(Ln2)

            elif Statue == "Self defined line used - case 3":
                Ln2  = df_L2.loc[((df_L2["P1"]==P2) & (df_L2["P2"]==P1)), "Ln"].item()
                ls_L.append(-Ln2)
                    
        ######### Create surface from list of line
        gmsh.model.geo.add_plane_surface([gmsh.model.geo.add_curve_loop(ls_L)], Sn)


############################# Model synchro
gmsh.model.geo.synchronize()

 
############################# Physical group
if df_P.shape[0] != 0:
    for GName in df_P["GName"].unique():
        ls_P = df_P.loc[df_P["GName"]==GName, "Pn"].tolist()
        gmsh.model.setPhysicalName(0, gmsh.model.addPhysicalGroup(0, ls_P), GName)
if df_L.shape[0] != 0:
    for GName in df_L["GName"].unique():
        ls_L = df_L.loc[df_L["GName"]==GName, "Ln"].tolist()
        gmsh.model.setPhysicalName(1, gmsh.model.addPhysicalGroup(1, ls_L), GName)
if df_S.shape[0] != 0:
    for GName in df_S["GName"].unique():
        ls_S = df_S.loc[df_S["GName"]==GName, "Sn"].tolist()
        gmsh.model.setPhysicalName(2, gmsh.model.addPhysicalGroup(2, ls_S), GName)


############################# Generate mesh
gmsh.model.geo.synchronize()
gmsh.model.mesh.generate()
gmsh.model.mesh.recombine()


############################# Write mesh data
gmsh.option.setNumber("Mesh.MshFileVersion", 2)
gmsh.write(folder_data + "Median.msh")
gmsh.finalize()




############################################################################### .export for ASTER
cwd    = os.getcwd()
ls_exp = []

ls_exp.append("P actions make_etude")
ls_exp.append("P memjob 1048576")
ls_exp.append("P memory_limit 1024.0")
ls_exp.append("P mode interactif")
ls_exp.append("P mpi_nbcpu 1")
ls_exp.append("P ncpus 1")
ls_exp.append("P rep_trav " + folder_expo + "temp")
ls_exp.append("P time_limit 900.0")
ls_exp.append("P tpsjob 16")
ls_exp.append("P version stable")
ls_exp.append("A memjeveux 128.0")
ls_exp.append("A tpmax 900.0")
ls_exp.append("F comm " + folder_expo + "Median.comm D  1")
ls_exp.append("F mmed " + folder_expo + "Median.msh D  20")
ls_exp.append("F mess " + folder_expo + "Output_Aster.mess R  6")
ls_exp.append("F resu " + folder_expo + "Output_Aster.resu R  80")

with open(folder_data + 'Median.export', 'w') as f:
    for line in ls_exp:
        f.write(line)
        f.write('\n')
        



############################################################################### .comm for ASTER
ls_com    = []

ls_com.append("######### Start")
ls_com.append("DEBUT();")

ls_com.append("######### Model definition")
ls_com.append("mesh=LIRE_MAILLAGE(INFO=2,UNITE=20,FORMAT='GMSH',);")

ls_com.append("mesh=DEFI_GROUP(")
ls_com.append("    MAILLAGE=mesh,")
ls_com.append("    reuse=mesh,")
ls_com.append("    CREA_GROUP_MA=_F(NOM='TOUT',TOUT='OUI',),")
ls_com.append("    CREA_GROUP_NO=_F(TOUT_GROUP_MA='OUI',),")
ls_com.append(");")

ls_com.append("model=AFFE_MODELE(")
ls_com.append("MAILLAGE=mesh,")
ls_com.append("    AFFE=(")
di_GNo = df_GNo.set_index("GName")["GNo"].to_dict()
for i in df_Propr_BC.index:
    GName = df_Propr_BC.loc[i, "GName"]
    GNo   = di_GNo[GName]
    EType = df_Propr_BC.loc[i, "EType"]
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),PHENOMENE='MECANIQUE',MODELISATION='" + str(EType) + "',),")
for i in df_Propr_SW.index:
    GName = df_Propr_SW.loc[i, "GName"]
    GNo   = di_GNo[GName]
    EType = df_Propr_SW.loc[i, "EType"]
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),PHENOMENE='MECANIQUE',MODELISATION='" + str(EType) + "',),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("######### Material definition")
ls_com.append("concrete=DEFI_MATERIAU(")
ls_com.append("    ELAS=_F(E=35e9, NU=0.2, RHO=2.5e3, ALPHA=12e-6,),")
ls_com.append(");")

ls_com.append("material=AFFE_MATERIAU(")
ls_com.append("    MAILLAGE=mesh,")
ls_com.append("    AFFE=(")
for i in df_Propr_BC.index:
    GName = df_Propr_BC.loc[i, "GName"]
    GNo   = di_GNo[GName]
    Mater = df_Propr_BC.loc[i, "Mater"]
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),MATER=" + str(Mater) + ",),")
for i in df_Propr_SW.index:
    GName = df_Propr_SW.loc[i, "GName"]
    GNo   = di_GNo[GName]
    Mater = df_Propr_SW.loc[i, "Mater"]
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),MATER=" + str(Mater) + ",),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("######### Section definition")
ls_com.append("elemcar=AFFE_CARA_ELEM(")
ls_com.append("    MODELE=model,")
ls_com.append("    POUTRE=(")
for i in df_Propr_BC.index:
    GName = df_Propr_BC.loc[i, "GName"]
    GNo   = di_GNo[GName]
    Thick = df_Propr_BC.loc[i, "Thick"]
    Thick_1, Thick_2, Thick_3 = Thick.replace(";",",").split("|")
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),SECTION=" + str(Thick_1) + ",CARA=(" + str(Thick_2) + "),VALE=(" + str(Thick_3) + ")),")
ls_com.append("    ),")
ls_com.append("    COQUE=(")
for i in df_Propr_SW.index:
    GName = df_Propr_SW.loc[i, "GName"]
    GNo   = di_GNo[GName]
    Thick = df_Propr_SW.loc[i, "Thick"]
    ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',),EPAIS=" + str(Thick) + ",VECTEUR=(1,0,0)),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("######### Limit condition definition")
ls_com.append("limco=AFFE_CHAR_MECA(")
ls_com.append("    MODELE=model,")
ls_com.append("    DDL_IMPO=(")

df_LimCo.loc[df_LimCo["Type"]=="FIXED", "LimCo"] = "DX=0,DY=0,DZ=0,DRX=0,DRY=0,DRZ=0"
for i in df_LimCo.index:
    GName = df_LimCo.loc[i, "GName"]
    GNo   = di_GNo[GName]
    LimCo = df_LimCo.loc[i, "LimCo"]
    ls_com.append("        _F(GROUP_NO=('" + str(GNo) + "',)," + str(LimCo) + "),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("######### Load definition")
df_Loads_F = df_Loads.loc[df_Loads["Type"].str[0]=="F"].copy()
df_Loads_F["Loads"] = df_Loads_F["Type"].astype(str) + "=" + df_Loads_F["Value"].astype(str)
if df_Loads_F.shape[0] != 0:
    ls_com.append("loads_f=AFFE_CHAR_MECA(")
    ls_com.append("    MODELE=model,")
    ls_com.append("    FORCE_NODALE=(")
    for i in df_Loads_F.index:
        GName = df_Loads_F.loc[i, "GName"]
        GNo   = di_GNo[GName]
        Loads = df_Loads_F.loc[i, "Loads"]
        ls_com.append("        _F(GROUP_NO=('" + str(GNo) + "',)," + str(Loads) + "),")
    ls_com.append("    ),")
    ls_com.append(");")
    
df_Loads_P = df_Loads.loc[df_Loads["Type"].str[0]=="P"].copy()
df_Loads_P["Loads"] = "PRES=" + df_Loads_P["Value"].astype(str)
if df_Loads_P.shape[0] != 0:
    ls_com.append("loads_p=AFFE_CHAR_MECA(")
    ls_com.append("    MODELE=model,")
    ls_com.append("    FORCE_COQUE=(")
    for i in df_Loads_P.index:
        GName = df_Loads_P.loc[i, "GName"]
        GNo   = di_GNo[GName]
        Loads = df_Loads_P.loc[i, "Loads"]
        ls_com.append("        _F(GROUP_MA=('" + str(GNo) + "',)," + str(Loads) + "),")
    ls_com.append("    ),")
    ls_com.append(");")

ls_com.append("######### Static calculation")
ls_com.append("stat=MECA_STATIQUE(")
ls_com.append("    MODELE=model,")
ls_com.append("    CHAM_MATER=material,")
ls_com.append("    CARA_ELEM=elemcar,")
ls_com.append("    INFO=2,")
ls_com.append("    EXCIT=(")
ls_com.append("        _F(CHARGE=limco,),")
if df_Loads_F.shape[0] != 0:
    ls_com.append("        _F(CHARGE=loads_f,),")
if df_Loads_P.shape[0] != 0:
    ls_com.append("        _F(CHARGE=loads_p,),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("stat=CALC_CHAMP(")
ls_com.append("    reuse=stat,")
ls_com.append("    RESULTAT=stat,")
ls_com.append("    CONTRAINTE=('EFGE_ELNO'),")
ls_com.append("    FORCE=('REAC_NODA'),")
ls_com.append(");")

ls_com.append("######### Output result")
ls_com.append("IMPR_RESU(")
ls_com.append("    FORMAT='RESULTAT', ")
ls_com.append("    UNITE=80,")
ls_com.append("    RESU=(")
group_out = df_GNo.loc[df_GNo["GName"].str[:4].isin(["Beam","Colu"]), "GName"]
if group_out.shape[0] != 0:
    group_out = str(group_out.map(di_GNo).tolist()).replace("[","").replace("]","")    
    ls_com.append("        _F(")
    ls_com.append("            RESULTAT=stat,")
    ls_com.append("            GROUP_MA=(" + group_out + "),")
    ls_com.append("	    TOUT_CHAM = 'OUI',")
    ls_com.append("	    FORM_TABL = 'EXCEL',")
    ls_com.append("	    IMPR_COOR = 'OUI',")
    ls_com.append("        ),")
group_out = df_GNo.loc[df_GNo["GName"].str[:4].isin(["Slab","Wall"]), "GName"]
if group_out.shape[0] != 0:
    group_out = str(group_out.map(di_GNo).tolist()).replace("[","").replace("]","")    
    ls_com.append("        _F(")
    ls_com.append("            RESULTAT=stat,")
    ls_com.append("            GROUP_MA=(" + group_out + "),")
    ls_com.append("	    TOUT_CHAM = 'OUI',")
    ls_com.append("	    FORM_TABL = 'EXCEL',")
    ls_com.append("	    IMPR_COOR = 'OUI',")
    ls_com.append("        ),")
ls_com.append("    ),")
ls_com.append(");")

ls_com.append("######### Ending")
ls_com.append("FIN();")

with open(folder_data + 'Median.comm', 'w') as f:
    for line in ls_com:
        f.write(line)
        f.write('\n')




# ############################################################################### Gmesh show
# if __name__ == '__main__':
#     # Execute when the module is not initialized from an import statement.
#     gmsh.initialize()
#     gmsh.open(folder_data + "Median.msh")
#     gmsh.fltk.run()
#     gmsh.finalize()
    
   	

