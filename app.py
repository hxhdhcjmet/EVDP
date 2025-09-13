from core import visualize as vs
from core import PreProcessing as pre
from core.predict import DataPredict as pred 
from core import quickPlot as plt
data=pre.load_data('d:/DeskTop/EVDP/core/data.xlsx')
wash_data=pre.clean_data(data)
predict=pred(wash_data,wash_data.iloc[:,0],wash_data.iloc[:,1],3)
predict.dataInterpolate(['spline'])
print(predict.interpolated_results)
plot=plt.pointLineChart(predict.new_x,predict.interpolated_results['spline'],save=False)






