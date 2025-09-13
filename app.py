from core import visualize as vs
from core import PreProcessing as pre
from core.predict import DataPredict as pred 
from core import quickPlot as plt
data=pre.load_data('d:/DeskTop/EVDP/core/data.xlsx')
wash_data=pre.clean_data(data)
predict=pred(wash_data,wash_data.iloc[:,0],wash_data.iloc[:,2],3)
predict.dataInterpolate(['linear'])











