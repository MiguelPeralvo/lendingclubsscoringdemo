import mlflow
import mlflow.sklearn
from pyspark.sql import Window
from pyspark.sql.functions import *
from pyspark.sql.types import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from lendingclub_scoring.data.DataProvider import LendingClubDataProvider



class LendingClubConsumerPipeline():
    def __init__(self, spark, input_path, output_path, model_name, limit=None):
        self.spark = spark
        self.input_path = input_path
        self.output_path = output_path
        self.model_name = model_name
        self.limit = limit
        self.data_provider = LendingClubDataProvider(spark, input_path, limit)

    def run(self):
        df = self.data_provider.load_and_transform_data_consumer()
        df.createOrReplaceTempView("loans")

        self.spark.udf.register("model", mlflow.pyfunc.spark_udf(self.spark, model_uri='models:/{}/Production'.format(self.model_name)))

        self.spark.sql("""
        select *, model(term, home_ownership, purpose, addr_state, verification_status, application_type, loan_amnt, emp_length,
         annual_inc,dti, delinq_2yrs, revol_util, total_acc, credit_length_in_years, int_rate, net, issue_year) as prediction 
        from loans
        """).write.format('delta').mode('overwrite').save(self.output_path)




