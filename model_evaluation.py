## Sample script for TI&R
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

def evaluate_model(y_pred_test_df_wide:pd.DataFrame,
                   horizon: str,
                   target_var:str,
                   parameters: dict,
                   freq = 'MS')->pd.DataFrame:
    """Compute MAE for different horizon

    Args:
         y_pred_test_df_wide: dataframe that contains test forecast in wide format
         

    Returns:
       y_pred_test_df_mae_wide_final which contains the MAE for all forecast.
    """
    #get the target name from parameter
    if freq == 'MS':
        freq_name = 'monthly'
    elif freq == 'SM':
        freq_name = 'biweekly'

    #target_var = parameters[f'{horizon}_{freq_name}_target_single_step'][0]

    #initialize empty data frame
    y_pred_test_df_mae_wide_final = pd.DataFrame()

    #define no of prediction
    no_of_prediction = 12 #get_no_of_predictions(horizon)

    if freq == 'SM':
        no_of_prediction *= 2

    #obtain list of models
    models = y_pred_test_df_wide['model'].unique()


    #loop through each model
    for i in range(len(models)):

        #subset specific models
        y_pred_test_df_mae_wide_sub = y_pred_test_df_wide[y_pred_test_df_wide['model']==models[i]].copy()

        #create dataframe to concat
        mae_combined = pd.DataFrame({'date_time': ['validation', 'test'],
                                    'model': [models[i], models[i]]})

        #loop through each horizon
        for j in range(no_of_prediction):

            #lag by horizon then compute MAE by period 
            #validation: 2016-2018
            #test: 2019-2021
            y_pred_test_df_mae_wide_sub[f'actual_M{j}'] = y_pred_test_df_mae_wide_sub[target_var].shift(-j)
            y_pred_test_df_mae_wide_sub[f'diff_M{j}'] = y_pred_test_df_mae_wide_sub[f'M{j}'] - y_pred_test_df_mae_wide_sub[f'actual_M{j}']
            y_pred_test_df_mae_wide_sub[f'abs_diff_M{j}'] = y_pred_test_df_mae_wide_sub[f'diff_M{j}'].abs()
            y_pred_test_df_mae_wide_sub[f'abs_diff_M{j}_lag_{j}'] = y_pred_test_df_mae_wide_sub[f'abs_diff_M{j}'].shift(j)
            mae_sub = pd.DataFrame(
                {
                    f'abs_diff_M{j}': [y_pred_test_df_mae_wide_sub[(y_pred_test_df_mae_wide_sub['date_time']>='2016-01-01') & (y_pred_test_df_mae_wide_sub['date_time']<'2019-01-01')][f'abs_diff_M{j}_lag_{j}'].mean(), 
                            y_pred_test_df_mae_wide_sub[y_pred_test_df_mae_wide_sub['date_time']>='2019-01-01'][f'abs_diff_M{j}_lag_{j}'].mean()]
                }
            )
            mae_combined = pd.concat([mae_combined, mae_sub],axis=1)

        #concat df
        y_pred_test_df_mae_wide_sub = pd.concat([y_pred_test_df_mae_wide_sub, mae_combined],axis = 0)
        y_pred_test_df_mae_wide_final = pd.concat([y_pred_test_df_mae_wide_final, y_pred_test_df_mae_wide_sub],axis = 0)
        
    #subset columns
    cols_sub = [col for col in y_pred_test_df_mae_wide_final.columns if 'abs_diff_M' in col]
    cols_sub = [col for col in cols_sub if 'lag' not in col]
    cols = ['date_time']
    cols.extend(cols_sub)
    cols.extend(['model'])
    y_pred_test_df_mae_wide_final = y_pred_test_df_mae_wide_final[cols]
    y_pred_test_df_mae_wide_final['average_mae'] = y_pred_test_df_mae_wide_final.sum(axis = 1)/no_of_prediction
    if horizon == 'short_term':
        # test_result = pd.read_csv('data/07_model_output/short_term_test_error.csv')
        # test_result_val_test = test_result[test_result['date_time'].str.contains("test|validation")]
        # test_result_val_test
        from datetime import datetime
        now = datetime.now()
        now = str(now).replace(' ','_').replace('-','').replace(':','').rsplit('.')[0]
        y_pred_test_df_mae_wide_final = y_pred_test_df_mae_wide_final.round(decimals=2)
        y_pred_test_df_mae_wide_final_val_test = y_pred_test_df_mae_wide_final[y_pred_test_df_mae_wide_final['date_time'].str.contains("test|validation",na=False)]
        if freq == 'SM':
            y_pred_test_df_mae_wide_final_val_test.to_csv(f'data/07_model_output/short_term_biweekly_test_error{now}.csv',index = False)
        else:
            y_pred_test_df_mae_wide_final_val_test.to_csv(f'data/07_model_output/short_term_test_error{now}.csv',index = False)

    #round to 2 decimal place
    y_pred_test_df_mae_wide_final = y_pred_test_df_mae_wide_final.round(decimals=2)

    return y_pred_test_df_mae_wide_final