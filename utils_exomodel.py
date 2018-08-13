import pandas as pd
import numpy as np
import random
from xgboost import XGBRegressor
from xgboost import plot_importance


def get_exochromoesome(df, models):
    bits_per_model = int(np.ceil(np.log2(len(models))))
    chromosome = ""
    for n_col in df.columns:
        for m_row in df.index:
            model = df.loc[m_row, n_col]
            model_position = models.index(model)
            chromosome = chromosome + "" + np.binary_repr(model_position, width= bits_per_model )
    return chromosome


def build_neuronal_system(M, N, models):
    n_columns =  list()
    for i in range(N):
        n_name = "N_" +str(i)
        n_columns.append(n_name)
    m_rows =  list()
    for j in range(M):
        m_name = "M_"+str(j)
        m_rows.append(m_name)

    neuronal_system = pd.DataFrame(columns =  n_columns, index = m_rows)
    for n_col in n_columns:
        for m_row in m_rows:
            neuronal_system.loc[m_row, n_col] = random.choice(models)

    chromosome = get_exochromoesome(neuronal_system, models)

    return neuronal_system, chromosome


def decode_neuronal_system(neuronal_system, df):
    """
    This funtion transforms the neuronal_system into a set of models that must be trained 
    in order to score the neuronal_system. NEURONAL_SOLUTIONS represent the neuronal network

    NEURONAL_SOLUTIONS[n_col][m_row] = indicates the characteristics of a particular neuron 
    at model_position n_col, m_row.
        Inside each neuron we find:
            * model_name: XGBoost, LR, RandomForest ...
            * model: sklearn object with the model for fit.
            * name: model_name + neuron position. This feature is usefull to identify 
                    the output of the neuron as imput of other neuron
            * baseline_features: The features inside the initial dataset. baseline_features doesn't
                    take into account the output of other neurons.
            * baseline_features_chormosome: The binary representation of the baseline_features.
                    Each fature is represented by one bit. If the model in the corresponded neuron
                    is choosen to be trained with baseline_fetaure X, then the position at X
                    for the baseline_features_chormosome must be equal to 1 (0 if it's not included)
            * exmodel: A dictionary that contains features from other models.
                    There is a entry for each layer in the model:
                          1 2 3
                         [][][][]  models in layer 1, con use output features from layer 0
                        [][][][]  models in layer 2, can use output features from layer 0,1 
                        [][][][]  ...
                        [][][][]  models in layer 3 can use output features from layer 0,1,2
                    * exmodel[layer][features]: For a particular layer, what variables will
                                  be used in the input neuron-model.
                                  **if layer of neuron < layer, non variable is included.
                    * exmodel[layer][chromosome]: representation of the features used
                                  in the neuron model from layer = layerX. 
                                  1 if output of layerX, neuron 1 included
                                  01 if output of layerX, neuron 2 included
                                  ...
                                  0001 if output of layerX, neuron 4 included.
    """
    NEURONAL_SOLUTIONS = dict()
    for i in range(len(neuronal_system.columns)):
        n_col = neuronal_system.columns[i]
        NEURONAL_SOLUTIONS[n_col] = dict()
        for j in range(len(neuronal_system.index)):
            m_row = neuronal_system.index[j]

            model = neuronal_system.loc[m_row, n_col]
            NEURONAL_SOLUTIONS[n_col][m_row] = dict()
            NEURONAL_SOLUTIONS[n_col][m_row]["model_name"] = model
            NEURONAL_SOLUTIONS[n_col][m_row]["model"] = fit_models[model]
            NEURONAL_SOLUTIONS[n_col][m_row]["name"] = model + "_" + str(n_col) + "_" + str(m_row)

            #For each model we want to test the features that should be included in the model. 
            features_number = len(df.columns)
            baseline_features = list()
            baseline_features_chormosome = ""
            for f in range(features_number):
                feature = df.columns[f]
                isincluded = random.choice([True,False])
                if isincluded:
                    baseline_features.append(feature)
                    baseline_features_chormosome += "1"
                else:
                    baseline_features_chormosome += "0"

            NEURONAL_SOLUTIONS[n_col][m_row]["baseline_features"] =  baseline_features
            NEURONAL_SOLUTIONS[n_col][m_row]["baseline_features_chormosome"] =  baseline_features_chormosome
            NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"] =  dict()
            

            #Include exmodel features for layers>0 
            for layer in neuronal_system.columns:
                NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer] = dict()
                if i <= int(layer.replace("N_", "")) or i ==0:
                    NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["features"] = []
                    NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["chromosome"] = ""
                else:

                    exmodel = list()
                    exmodel_chormosome = ""
                    for j_2 in range(len(neuronal_system.index)):
                        m_row_asfeature = neuronal_system.index[j_2]
                        feature = NEURONAL_SOLUTIONS[layer][m_row_asfeature]["name"]
                        isincluded = random.choice([True,False])

                        if isincluded and NEURONAL_SOLUTIONS[layer][m_row_asfeature]["model_name"] != "":
                            exmodel.append(feature)
                            exmodel_chormosome += "1"
                        else:
                            exmodel_chormosome += "0"

                    NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["features"]   = exmodel
                    NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["chromosome"] = exmodel_chormosome

    return NEURONAL_SOLUTIONS


def decode_exochromosome(M, N , chromosome, models):
    bits_per_model = int(np.ceil(np.log2(len(models))))

    n_columns =  list()
    for i in range(N):
        n_name = "N_" +str(i)
        n_columns.append(n_name)
    m_rows =  list()
    for j in range(M):
        m_name = "M_"+str(j)
        m_rows.append(m_name)

    neuronal_system = pd.DataFrame(columns =  n_columns, index = m_rows)
    for i in range(len(n_columns)):
        n_col =  n_columns[i]
        for j in range(len(m_rows)):
            m_row = m_rows[j]
            neuronal_system.loc[m_row, n_col] = chromosome[(i*len(m_rows)*bits_per_model)+ (j*bits_per_model) : (i*len(m_rows)*bits_per_model)+ (j*bits_per_model) +bits_per_model]

    return chromosome



def get_intramodel_chromosomes(NEURONAL_SOLUTIONS):
    """
    return a chromosome that represents the features that will be used to fit the 
    model inside a neuron.
    baseline_features   +   layer0_feature   + layer1_features + ... + layern_features
    [][][][][][][][]        [][][][][][][]     [][][][][][][][]        [][][][][][][]
                            
                            1 bit per neuron    1 bit per neuron
                            in layer 0.         in layer 1.

     """
    for n_col in NEURONAL_SOLUTIONS.keys():
        for m_row in NEURONAL_SOLUTIONS[n_col].keys():
            intramodel_chromosome = ""
            intramodel_chromosome += NEURONAL_SOLUTIONS[n_col][m_row]["baseline_features_chormosome"]
            for i in range(len(NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"].keys())):
                layer = "N_" +  str(i)
                intramodel_chromosome += NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["chromosome"]
            NEURONAL_SOLUTIONS[n_col][m_row]["intramodel_chromosome"] = intramodel_chromosome


def get_intramodel_features(NEURONAL_SOLUTIONS, LAYER):
    """
    This function use the exmodel_chormosome of NEURON Z to return output of the
    NEURON Y model  as an input for NEURON Z.
    This function must be applied in order beacause it requieres that the output of NEURON Y
    is ready to be used by NEURON Z.

    in a NEURONAL_SOLUTIONS system of 4X4:
                            layer0       layer1     layer2   layer3
    exmodel_chormosome: [1][0][0][1] [0][0][1][1] [][][][] [][][][]

    In this exmple NEURON Z needs the output neuron0 and neuron3 of layer1
                            needs the output of neuron2 and neuron3 of layer2
                            don't need any input from layer2 and layer3.


    1. Make a data DataFrame with the output of all the neuron models for layer<LAYER
    2. Use the exmodel as a index for the DataFrame in 1.
    3. Merge 3 with baseline_features.

    """

    all_exmodel_features = pd.DataFrame()
    for n_col in range(NEURONAL_SOLUTIONS.keys()):
        if n_col < int(LAYER.replace("N_", "")):
            name = NEURONAL_SOLUTIONS[n_col][m_row]["name"]
            all_exmodel_features[name] = NEURONAL_SOLUTIONS[n_col][m_row]["output"]

    for m_row in NEURONAL_SOLUTIONS[LAYER].keys():
        exmodel_features = list()
        for layer in NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel"].keys():
            exmodel_features.append(NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel"][layer]["features"])

        NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel_features"] = exmodel_features
        NEURONAL_SOLUTIONS[LAYER][m_row]["all_features"] = exmodel_features.append(NEURONAL_SOLUTIONS[LAYER][m_row]["baseline_features"])
        NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel_DataFrame"] = all_exmodel_features[NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel_features"]]
        
        NEURONAL_SOLUTIONS[LAYER][m_row]["all_DataFrame"] = df[NEURONAL_SOLUTIONS[LAYER][m_row]["baseline_features"]]\
                                                            .merge(NEURONAL_SOLUTIONS[LAYER][m_row]["exmodel_DataFrame"], \
                                                            right_index =True, left_index = True) 

    return all_exmodel_features

def simulate_output(NEURONAL_SOLUTIONS, layer, df_kfolded):
    """
    Fills NEURONAL_SOLUTIONS[n_col][m_row]["output"]
    With a simulated output of len(df).
    """
    for n_col in NEURONAL_SOLUTIONS.keys():
        if int(n_col.replace("N_", "")) < layer:
            for m_row in NEURONAL_SOLUTIONS[n_col].keys():
                NEURONAL_SOLUTIONS[n_col][m_row]["output"] = dict()
                NEURONAL_SOLUTIONS[n_col][m_row]["output"]["all_data"]    = list()
                for fold in df_kfolded.keys():
                    NEURONAL_SOLUTIONS[n_col][m_row]["output"][fold] = np.random.rand( len(df_kfolded[fold]["data"]))
                    NEURONAL_SOLUTIONS[n_col][m_row]["output"]["all_data"].extend(NEURONAL_SOLUTIONS[n_col][m_row]["output"][fold])


def get_models_output(NEURONAL_SOLUTIONS, df_kfolded):
    """
    For LAYER N > 0, some models may need the predictions of previous models.
    this function returns df_output wich contains an entry for every fold and for 
    the complete data that presents all the output or predictions from the previous
    model as a DataFrame.

    df_output[fold] = NEURONAL_SOLUTIONS[n_col][m_row]["output][fold] for all n_col, m_row

    """
    df_output = dict()
    for fold in df_kfolded.keys():
        df_output[fold] = pd.DataFrame()
        for n_col in NEURONAL_SOLUTIONS.keys():
            for m_row in NEURONAL_SOLUTIONS[n_col].keys():
                name    = NEURONAL_SOLUTIONS[n_col][m_row]["name"]
                index   = df_kfolded[fold]["index"]
                output  = NEURONAL_SOLUTIONS[n_col][m_row]["output"][fold]
                df_fold = pd.DataFrame( data = output, index =  index, columns = [name])
                #print(df_fold.head())
                if len(df_output[fold]) == 0:
                    df_output[fold] = df_fold
                    print(df_output[fold].shape)
                else:
                    df_output[fold] = df_output[fold].merge(df_fold, right_index = True, left_index = True)
                    print(df_output[fold].shape)
    return df_output


def get_exmodel_features(NEURONAL_SOLUTIONS):
    """
    Append all exmodel output features names to call them from the df_output dataset.
    """
    for n_col in NEURONAL_SOLUTIONS.keys():
        for m_row in NEURONAL_SOLUTIONS[n_col].keys():
            NEURONAL`_SOLUTIONS[n_col][m_row]["exmodel_features"] = list()
            for layer in NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"].keys()
                NEURONAL_SOLUTIONS[n_col][m_row]["exmodel_features"].append(NEURONAL_SOLUTIONS[n_col][m_row]["exmodel"][layer]["features"])

def  transform_KFold(df, K):
    """
    Divides a DataFrame into K sets using the index. 
    df_kfolded[fold_number]
        df_kfolded[fold_number]["index"]: randomly selected index 
                                          for fold_number fold.
        df_kfolded[fold_number]["data]:  subset of the DataFrame indexed
                                         by the selected index.
        df_kfolded["all_data"][...]
    """
    df = df.reset_index()
    all_index =  df.index
    df_kfolded = dict()
    obs_per_fold = int(np.round(len(df)/K))

    for k in range(K):
        print("K: {}  all_index: {} ".format(k, len(all_index)))
        df_kfolded[k] = dict()
        df_copy = df.copy()
        if k == K-1:
            df_kfolded[k]["data"]  = df_copy.loc[all_index]
            df_kfolded[k]["index"] = all_index
        else:

            fold_index = np.random.choice(all_index, obs_per_fold, replace= False)
            fold_data = df_copy.loc[fold_index]
            all_index = [item for item in all_index if item not in fold_index]

            df_kfolded[k]["index"] = fold_index
            df_kfolded[k]["data"]  = fold_data
        print( len(df_kfolded[k]["index"]))

    df_copy = df.copy()

    df_kfolded["all_data"] = dict()
    df_kfolded["all_data"]["data"]  =  df_copy
    df_kfolded["all_data"]["index"] =  df.index

    return df_kfolded

#------------------------------------MODELS----------------------------------------------

fit_models = {"":np.nan , 
              "XGBoost":XGBRegressor(max_depth=14, 
                        learning_rate=0.15, #learning_rate=0.05
                        n_estimators=800, 
                        silent=True, 
                        objective='reg:linear', 
                        nthread=32, 
                        gamma=0,
                        min_child_weight=1, 
                        max_delta_step=0, 
                        subsample=0.85, 
                        colsample_bytree=0.7, 
                        colsample_bylevel=1, 
                        reg_alpha=0, 
                        reg_lambda=1, 
                        scale_pos_weight=1, 
                        seed=1440, 
                        missing=None) , 
              "LR":1,
              "RandomForest":2,
              "LGBM": 3}


#-----------------------------Upload INFO and get training sets-----------------------------------
df = pd.read_csv('/home/coronado/Desktop/clustnet/Data/df_elglobo_sample.csv')
df_kfolded = transform_KFold(df, 5)


Y = df.VentaUnidades
del df["VentaUnidades"]
models = ["", "XGBoost", "LR", "RandomForest", "LGBM"]
M= 4     
N= 4

neuronal_system, chromosome = build_neuronal_system(M, N, models)
NEURONAL_SOLUTIONS = decode_neuronal_system(neuronal_system, df)
get_intramodel_chromosomes(NEURONAL_SOLUTIONS)
simulate_output(NEURONAL_SOLUTIONS, N, df_kfolded)
df_output = get_models_output(NEURONAL_SOLUTIONS, df_kfolded) #runs everytime a layer is finished.
get_exmodel_features(NEURONAL_SOLUTIONS)

for fold in df_kfolded.keys():
for n_col in NEURONAL_SOLUTIONS.keys():
    for m_row in NEURONAL_SOLUTIONS[n_col].keys():
        print("\n\nSolving LAYER: {} - ROW: {}  \n\tNEURON: {}".format(n_col, m_row, NEURONAL_SOLUTIONS[n_col][m_row]["name"]))

        #Dont need output from other neurons.
        df_base = df_kfolded[fold]["data"][[NEURONAL_SOLUTIONS[n_col][m_row]["baseline_features"]]
        df_model = df_output[fold][[NEURONAL_SOLUTIONS[n_col][m_row]["exmodel_features"]]
        df_train_fold = df_base.merge(df_model, right_index = True , left_index = True)
        NEURONAL_SOLUTIONS[n_col][m_row]["train_dataset"][fold] = df_train_fold
