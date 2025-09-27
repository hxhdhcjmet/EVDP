from core import visualize as vs
from core import PreProcessing as pre
from core.predict import DataPredict as pred 
from core import quickPlot as plt
data=pre.load_data('d:/DeskTop/test.xlsx')
wahsed_data=pre.clean_data(data)
prediction=pred(wahsed_data,wahsed_data.iloc[:,1],wahsed_data.iloc[:,2])
prediction.train_model('random_forest')
prediction.visualize_predict_result(wahsed_data.iloc[:,1],wahsed_data.iloc[:,2],prediction.prediction_results['random_forest'],'random_forest')












