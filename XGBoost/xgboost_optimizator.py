"""
General Parameters: Guide the overall functioning
These define the overall functionality of XGBoost.

booster [default=gbtree]
	Select the type of model to run at each iteration. It has 2 options:
	gbtree: tree-based models
	gblinear: linear models <----- This kind of booster is never used.

silent [default=0]:
	Silent mode is activated is set to 1, i.e. no running messages will be printed.
	It’s generally good to keep it 0 as the messages might help in understanding the model.

nthread [default to maximum number of threads available if not set]
	This is used for parallel processing and number of cores in the system should be entered
	If you wish to run on all cores, value should not be entered and algorithm will detect automatically
	There are 2 more parameters which are set automatically by XGBoost and you need not worry about them. Lets move on to Booster parameters.




Booster Parameters: Guide the individual booster (tree/regression) at each step
eta [default=0.3]
	Analogous to learning rate in GBM
	Makes the model more robust by shrinking the weights on each step
	Typical final values to be used: 0.01-0.2

min_child_weight [default=1]
	Defines the minimum sum of weights of all observations required in a child.
	This is similar to min_child_leaf in GBM but not exactly. This refers to min “sum of weights” of observations while GBM has min “number of observations”.
	Used to control over-fitting. Higher values prevent a model from learning relations which might be highly specific to the particular sample selected for a tree.
	Too high values can lead to under-fitting hence, it should be tuned using CV.

max_depth [default=6]
	The maximum depth of a tree, same as GBM.
	Used to control over-fitting as higher depth will allow model to learn relations very specific to a particular sample.
	Should be tuned using CV.
	Typical values: 3-10

max_leaf_nodes
	The maximum number of terminal nodes or leaves in a tree.
	Can be defined in place of max_depth. Since binary trees are created, a depth of ‘n’ would produce a maximum of 2^n leaves.
	If this is defined, GBM will ignore max_depth.

gamma [default=0]
	A node is split only when the resulting split gives a positive reduction in the loss function. Gamma specifies the minimum loss reduction required to make a split.
	Makes the algorithm conservative. The values can vary depending on the loss function and should be tuned.

max_delta_step [default=0]
	In maximum delta step we allow each tree’s weight estimation to be. If the value is set to 0, it means there is no constraint. If it is set to a positive value, it can help making the update step more conservative.
	Usually this parameter is not needed, but it might help in logistic regression when class is extremely imbalanced.
	This is generally not used but you can explore further if you wish.

subsample [default=1]
	Same as the subsample of GBM. Denotes the fraction of observations to be randomly samples for each tree.
	Lower values make the algorithm more conservative and prevents overfitting but too small values might lead to under-fitting.
	Typical values: 0.5-1

colsample_bytree [default=1]
	Similar to max_features in GBM. Denotes the fraction of columns to be randomly samples for each tree.
	Typical values: 0.5-1

colsample_bylevel [default=1]
	Denotes the subsample ratio of columns for each split, in each level.
	I don’t use this often because subsample and colsample_bytree will do the job for you. but you can explore further if you feel so.

lambda [default=1]
	L2 regularization term on weights (analogous to Ridge regression)
	This used to handle the regularization part of XGBoost. Though many data scientists don’t use it often, it should be explored to reduce overfitting.

alpha [default=0]
	L1 regularization term on weight (analogous to Lasso regression)
	Can be used in case of very high dimensionality so that the algorithm runs faster when implemented

scale_pos_weight [default=1]
	A value greater than 0 should be used in case of high class imbalance as it helps in faster convergence.




Learning Task Parameters: Guide the optimization performed

objective [default=reg:linear]
	This defines the loss function to be minimized. Mostly used values are:
		binary:logistic –logistic regression for binary classification, returns predicted probability (not class)
		multi:softmax –multiclass classification using the softmax objective, returns predicted class (not probabilities)
		you also need to set an additional num_class (number of classes) parameter defining the number of unique classes
		multi:softprob –same as softmax, but returns predicted probability of each data point belonging to each class.

eval_metric [ default according to objective ]
	The metric to be used for validation data.
	The default values are rmse for regression and error for classification.
	Typical values are:
		rmse     – root mean square error
		mae      – mean absolute error
		logloss  – negative log-likelihood
		error    – Binary classification error rate (0.5 threshold)
		merror   – Multiclass classification error rate
		mlogloss – Multiclass logloss
		auc      – Area under the curve

seed [default=0]
The random number seed.
Can be used for generating reproducible results and also for parameter tuning.

"""



def modelfit(alg, dtrain, predictors, useTrainCV=True, cv_folds=5, early_stopping_rounds=50):
    
    if useTrainCV:
        xgb_param = alg.get_xgb_params()
        xgtrain   = xgb.DMatrix(dtrain[predictors].values, label=dtrain[target].values)
        cvresult  = xgb.cv(xgb_param, xgtrain, num_boost_round=alg.get_params()['n_estimators'], 
        	nfold=cv_folds,
            metrics='auc', 
            early_stopping_rounds=early_stopping_rounds, 
            show_progress=False)
        
        alg.set_params(n_estimators=cvresult.shape[0])
    
    #Fit the algorithm on the data
    alg.fit(dtrain[predictors], dtrain['Disbursed'],eval_metric='auc')
        
    #Predict training set:
    dtrain_predictions = alg.predict(dtrain[predictors])
    dtrain_predprob = alg.predict_proba(dtrain[predictors])[:,1]
        
    #Print model report:
    print "\nModel Report"
    print "Accuracy : %.4g" % metrics.accuracy_score(dtrain['Disbursed'].values, dtrain_predictions)
    print "AUC Score (Train): %f" % metrics.roc_auc_score(dtrain['Disbursed'], dtrain_predprob)
                    
    feat_imp = pd.Series(alg.booster().get_fscore()).sort_values(ascending=False)
    feat_imp.plot(kind='bar', title='Feature Importances')
    plt.ylabel('Feature Importance Score')