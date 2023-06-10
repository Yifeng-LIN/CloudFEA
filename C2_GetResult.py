import os
import pandas as pd
import numpy as np
from pandas import DataFrame, concat
import sys





################################################################################################
############################################################################### Parameter
################################################################################################
folder_name = "data_20230510090201_0001"
system      = "Win"  if sys.platform=="win32" else "Linux"

folder_data = "D:\\calculhub\\autodim_dash\\data\\"+folder_name+"\\" if system=="Win" else "/home/tirazone/calculhub/autodim/data/"+folder_name+"/"





################################################################################################
############################################################################### Code
################################################################################################

###########################################################################################
################################## Read group
####### Read
df_msh      = pd.read_csv(folder_data + "Median.msh", header=None)
df_GNo      = pd.read_csv(folder_data + "Input_df_GNo.csv", index_col=None)
df_Propr_BC = pd.read_csv(folder_data + "Input_df_Propr_BC.csv", index_col=None)
df_Propr_SW = pd.read_csv(folder_data + "Input_df_Propr_SW.csv", index_col=None)


####### Get element info
idxs    = df_msh.loc[df_msh.iloc[:,0].str.contains("Elements")].index
idx_sta = idxs[0] + 2
idx_end = idxs[1]
df_grop = df_msh[idx_sta: idx_end].iloc[:,0].str.split(expand=True).reset_index(drop=True).copy()


####### Fill to standard format
df_grop = df_grop.fillna(-999).copy()
for i in range(100):
    nb_col  = df_grop.shape[1]
    if nb_col < 9: df_grop[[nb_col]] = -999
df_grop.columns = ["ELEMENT","C2","C3","GNo_ini","Geo_Entity","N1","N2","N3","N4"]
df_grop         = df_grop[["ELEMENT","GNo_ini","Geo_Entity","N1","N2","N3","N4"]].copy()
df_grop         = df_grop.astype(int)
df_grop["GNo"]  = "GM" + df_grop["GNo_ini"].astype(str).copy()
df_grop["GName"] = df_grop["GNo"].map(df_GNo.set_index("GNo")["GName"].to_dict())
di_grop         = df_grop.set_index("ELEMENT").to_dict()


####### Get different group
df_E_GP = DataFrame()
df_E_GL = DataFrame()
df_E_GS = DataFrame()

df_tmp = df_grop.loc[( (df_grop[["N1"]]!=-999).all(axis=1) & (df_grop[["N2","N3","N4"]]==-999).all(axis=1) )]
if df_tmp.shape[0] != 0: df_E_GP = df_tmp.copy()
df_E_GP = df_E_GP.drop(columns=["N2","N3","N4"]).reset_index(drop=True).copy()

df_tmp = df_grop.loc[( (df_grop[["N1","N2"]]!=-999).all(axis=1) & (df_grop[["N3","N4"]]==-999).all(axis=1) )]
if df_tmp.shape[0] != 0: df_E_GL = df_tmp.copy()
df_E_GL = df_E_GL.drop(columns=["N3","N4"]).reset_index(drop=True).copy()

df_tmp = df_grop.loc[(df_grop[["N1","N2","N3","N4"]]!=-999).all(axis=1)]
if df_tmp.shape[0] != 0: df_E_GS = df_tmp.copy()
df_E_GS = df_E_GS.reset_index(drop=True).copy()




###########################################################################################
################################## Read Output pretreat
df_read = pd.read_csv(folder_data + "Output_Aster.resu", header=None)

df_idx = DataFrame(df_read.loc[df_read.iloc[:,0].str.contains("------>")].index, columns=["idx1"])
df_idx["idx2"] = df_idx["idx1"].shift(-1).fillna(df_read.shape[0]+1).astype(int)

df_c_idx = DataFrame(df_read.loc[df_read.iloc[:,0].str.contains("------>")].index + 1, columns=["c_idx"])
for i in df_c_idx.index:
    c_idx  = df_c_idx.loc[i, "c_idx"]
    c_text = df_read.loc[c_idx].item()
    c_text = c_text.replace("CHAMP AUX NOEUDS DE NOM SYMBOLIQUE","")
    c_text = c_text.replace("CHAMP PAR ELEMENT AUX NOEUDS DE NOM SYMBOLIQUE","")
    c_text = c_text.replace("CHAMP PAR ELEMENT AUX POINTS DE GAUSS DE NOM SYMBOLIQUE","")
    c_text = c_text.replace(" ","")
    c_text = c_text.replace(" ","")
    df_c_idx.loc[i, "CHAMP"] = c_text
    df_idx.loc[df_idx["idx1"] == c_idx-1, "CHAMP"] = c_text

sep_idx  = df_read.loc[df_read.iloc[:,0].str.contains("======>")].index.tolist()[-1]
df_idx.loc[df_idx["idx1"] <  sep_idx, "CompType"] = "BC"
df_idx.loc[df_idx["idx1"] >= sep_idx, "CompType"] = "SW"
df_idx["CHAMP_BCSW"] = df_idx["CHAMP"].str[:] + "_" + df_idx["CompType"].str[:]

di_read = {}
for i in df_idx.index:
    idx1, idx2, ch, ct, type_item = df_idx.loc[i]
    di_read[type_item]            = df_read.iloc[idx1+3:idx2].reset_index(drop=True)

    


###########################################################################################
################################## DEP_BC_NODE
type_item   = "DEPL_BC"
df          = di_read[type_item]
idx_empty   = df.loc[df.iloc[:,0].str[:5]=="     "].index
idx_embef   = idx_empty - 1
dfL         = df.loc[idx_embef].reset_index(drop=True)
dfL         = dfL.iloc[:,0].str.split(expand=True)
dfL.columns = dfL.iloc[0,:]
dfR         = df.loc[idx_empty].reset_index(drop=True)
dfR         = dfR.iloc[:,0].str.split(expand=True)
dfR.columns = dfR.iloc[0,:]
df_tmp      = dfL.join(dfR)

####### Treat particular
df_new      = df_tmp.loc[df_tmp["X"]!="X"].reset_index(drop=True).copy()

####### Change name
df_new["NOEUD"]   = df_new["NOEUD"].str.replace("N", "").astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].astype(float).astype(int)
df_new = df_new.rename({'NOEUD': 'NODE'}, axis='columns')
df_new            = df_new.astype(float)
df_new["NODE"]    = df_new["NODE"].astype(int)

####### Create df champ
df_DEP_BC_NODE   = df_new.copy()
df_DEP_BC_NODE.to_csv(folder_data + "Output_rs_DEP_BC_NODE.csv", index=None)




################################## MNT_BC_NODE
type_item   = "EFGE_ELNO_BC"
df          = di_read[type_item]
idx_empty   = df.loc[df.iloc[:,0].str[:5]=="     "].index
idx_embef   = idx_empty - 1
dfL         = df.loc[idx_embef].reset_index(drop=True)
dfL         = dfL.iloc[:,0].str.split(expand=True)
dfL.columns = dfL.iloc[0,:]
dfR         = df.loc[idx_empty].reset_index(drop=True)
dfR         = dfR.iloc[:,0].str.split(expand=True)
dfR.columns = dfR.iloc[0,:]
df_tmp      = dfL.join(dfR)

####### Treat particular
df_tmp1     = df_tmp.iloc[:,[0,0]]
df_tmp1.columns = ["ELEMENT","NOEUD"]
df_tmp2     = df_tmp.iloc[:,1:]
df_new      = df_tmp1.join(df_tmp2)
df_new.loc[df_new["ELEMENT"].str.contains("N"), "ELEMENT"] = np.nan
df_new      = df_new.fillna(method="ffill").copy()
df_new      = df_new.loc[df_new["X"]!="X"].reset_index(drop=True).copy()

####### Change name
df_new["ELEMENT"] = df_new["ELEMENT"].str.replace("M", "")
df_new["ELEMENT"] = df_new["ELEMENT"].astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].str.replace("N", "").astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].astype(float).astype(int)
df_new = df_new.rename({'NOEUD': 'NODE'}, axis='columns')
df_new            = df_new.astype(float)
df_new["NODE"]    = df_new["NODE"].astype(int)
df_new["ELEMENT"] = df_new["ELEMENT"].astype(int)

####### Change unit
df_new[['N', 'VY', 'VZ', 'MT', 'MFY', 'MFZ']] = (df_new[['N', 'VY', 'VZ', 'MT', 'MFY', 'MFZ']]/1000000).copy()

####### Create df champ
df_MNT_BC_NODE   = df_new.copy()
df_MNT_BC_NODE["GName"] = df_MNT_BC_NODE["ELEMENT"].map(di_grop["GName"])
df_MNT_BC_NODE = df_MNT_BC_NODE.loc[((df_MNT_BC_NODE["GName"].str[:4]=="Beam") | (df_MNT_BC_NODE["GName"].str[:4]=="Colu"))].reset_index(drop=True).copy()
df_MNT_BC_NODE.to_csv(folder_data + "Output_rs_MNT_BC_NODE.csv", index=None)




################################## MNT_BC_ELEM
col            = ['X', 'Y', 'Z', 'N', 'VY', 'VZ', 'MT', 'MFY', 'MFZ']
df_MNT_BC_ELEM = df_MNT_BC_NODE.groupby("ELEMENT")[col].mean().reset_index()
df_MNT_BC_ELEM["GName"] = df_MNT_BC_ELEM["ELEMENT"].map(di_grop["GName"])
df_MNT_BC_ELEM["ELEMENT"] = df_MNT_BC_ELEM["ELEMENT"].astype(int)

####### Add N1 N2 N3 N4 Thick for df_MNT
df_tmp         = df_MNT_BC_NODE[["ELEMENT","NODE","X","Y","Z"]].copy()
df_tmp["No"]   = df_tmp.index % 2
df_MNT_BC_ELEM_tmp = DataFrame()
for i in range(2):
    df_tmp_i   = df_tmp.loc[df_tmp["No"]==i, ["ELEMENT","NODE","X","Y","Z"]].set_index("ELEMENT").copy()
    df_tmp_i.columns = df_tmp_i.columns.str[:] + "_" + str(i+1)
    df_MNT_BC_ELEM_tmp  = concat([df_MNT_BC_ELEM_tmp, df_tmp_i], axis=1).copy()
df_MNT_BC_ELEM = concat([df_MNT_BC_ELEM.set_index("ELEMENT"), df_MNT_BC_ELEM_tmp], axis=1).reset_index().copy()
df_Propr_BC[["HY","HZ"]] = df_Propr_BC.iloc[:,-1].str.split("|",expand=True).iloc[:,-1].str.split(";",expand=True).copy()
df_MNT_BC_ELEM["HY"] = df_MNT_BC_ELEM["GName"].map(df_Propr_BC.set_index("GName").to_dict()["HY"])
df_MNT_BC_ELEM["HZ"] = df_MNT_BC_ELEM["GName"].map(df_Propr_BC.set_index("GName").to_dict()["HZ"])
df_MNT_BC_ELEM["Section"] = ("S-H" + ((df_MNT_BC_ELEM["HZ"].astype(float))*100).astype(int).astype(str).str.zfill(3) +\
                             "-W" +  ((df_MNT_BC_ELEM["HY"].astype(float))*100).astype(int).astype(str).str.zfill(3))
df_MNT_BC_ELEM.to_csv(folder_data + "Output_rs_MNT_BC_ELEM.csv", index=None)




###########################################################################################
################################## DEP_SW_NODE
type_item   = "DEPL_SW"
df          = di_read[type_item]
idx_empty   = df.loc[df.iloc[:,0].str[:5]=="     "].index
idx_embef   = idx_empty - 1
dfL         = df.loc[idx_embef].reset_index(drop=True)
dfL         = dfL.iloc[:,0].str.split(expand=True)
dfL.columns = dfL.iloc[0,:]
dfR         = df.loc[idx_empty].reset_index(drop=True)
dfR         = dfR.iloc[:,0].str.split(expand=True)
dfR.columns = dfR.iloc[0,:]
df_tmp      = dfL.join(dfR)

####### Treat particular
df_new      = df_tmp.loc[df_tmp["X"]!="X"].reset_index(drop=True).copy()

####### Change name
df_new["NOEUD"]   = df_new["NOEUD"].str.replace("N", "").astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].astype(float).astype(int)
df_new = df_new.rename({'NOEUD': 'NODE'}, axis='columns')
df_new            = df_new.astype(float)
df_new["NODE"]    = df_new["NODE"].astype(int)

####### Create df champ
df_DEP_SW_NODE   = df_new.copy()
df_DEP_SW_NODE.to_csv(folder_data + "Output_rs_DEP_SW_NODE.csv", index=None)




################################## MNT_SW_NODE
type_item   = "EFGE_ELNO_SW"
df          = di_read[type_item]
idx_empty   = df.loc[df.iloc[:,0].str[:5]=="     "].index
idx_embef   = idx_empty - 1
dfL         = df.loc[idx_embef].reset_index(drop=True)
dfL         = dfL.iloc[:,0].str.split(expand=True)
dfL.columns = dfL.iloc[0,:]
dfR         = df.loc[idx_empty].reset_index(drop=True)
dfR         = dfR.iloc[:,0].str.split(expand=True)
dfR.columns = dfR.iloc[0,:]
df_tmp      = dfL.join(dfR)

####### Treat particular
df_tmp1     = df_tmp.iloc[:,[0,0]]
df_tmp1.columns = ["ELEMENT","NOEUD"]
df_tmp2     = df_tmp.iloc[:,1:]
df_new      = df_tmp1.join(df_tmp2)
df_new.loc[df_new["ELEMENT"].str.contains("N"), "ELEMENT"] = np.nan
df_new      = df_new.fillna(method="ffill").copy()
df_new      = df_new.loc[df_new["X"]!="X"].reset_index(drop=True).copy()

####### Change name
df_new["ELEMENT"] = df_new["ELEMENT"].str.replace("M", "")
df_new["ELEMENT"] = df_new["ELEMENT"].astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].str.replace("N", "").astype(float).astype(int)
df_new["NOEUD"]   = df_new["NOEUD"].astype(float).astype(int)
df_new = df_new.rename({'NOEUD': 'NODE'}, axis='columns')
df_new            = df_new.astype(float)
df_new["NODE"]    = df_new["NODE"].astype(int)
df_new["ELEMENT"] = df_new["ELEMENT"].astype(int)

####### Change unit
df_new[['NXX', 'NYY', 'NXY', 'MXX', 'MYY', 'MXY', 'QX', 'QY']] = (df_new[['NXX', 'NYY', 'NXY', 'MXX', 'MYY', 'MXY', 'QX', 'QY']]/1000000).copy()

####### Create df champ
df_MNT_SW_NODE   = df_new.copy()
df_MNT_SW_NODE["GName"] = df_MNT_SW_NODE["ELEMENT"].map(di_grop["GName"])
df_MNT_SW_NODE.to_csv(folder_data + "Output_rs_MNT_SW_NODE.csv", index=None)




################################## MNT_SW_ELEM
col            = ['X', 'Y', 'Z', 'NXX', 'NYY', 'NXY', 'MXX', 'MYY', 'MXY', 'QX', 'QY']
df_MNT_SW_ELEM = df_MNT_SW_NODE.groupby("ELEMENT")[col].mean().reset_index()
df_MNT_SW_ELEM["GName"] = df_MNT_SW_ELEM["ELEMENT"].map(di_grop["GName"])
df_MNT_SW_ELEM["ELEMENT"] = df_MNT_SW_ELEM["ELEMENT"].astype(int)

####### Add N1 N2 N3 N4 Thick for df_MNT
df_tmp         = df_MNT_SW_NODE[["ELEMENT","NODE","X","Y","Z"]].copy()
df_tmp["No"]   = df_tmp.index % 4
df_MNT_SW_ELEM_tmp = DataFrame()
for i in range(4):
    df_tmp_i   = df_tmp.loc[df_tmp["No"]==i, ["ELEMENT","NODE","X","Y","Z"]].set_index("ELEMENT").copy()
    df_tmp_i.columns = df_tmp_i.columns.str[:] + "_" + str(i+1)
    df_MNT_SW_ELEM_tmp  = concat([df_MNT_SW_ELEM_tmp, df_tmp_i], axis=1).copy()
df_MNT_SW_ELEM = concat([df_MNT_SW_ELEM.set_index("ELEMENT"), df_MNT_SW_ELEM_tmp], axis=1).reset_index().copy()
df_MNT_SW_ELEM["HZ"] = df_MNT_SW_ELEM["GName"].map(df_Propr_SW.set_index("GName").to_dict()["Thick"])
df_MNT_SW_ELEM["Section"] = ("S-H" + ((df_MNT_SW_ELEM["HZ"].astype(float))*100).astype(int).astype(str).str.zfill(3) +\
                             "-W000")
df_MNT_SW_ELEM.to_csv(folder_data + "Output_rs_MNT_SW_ELEM.csv", index=None)





