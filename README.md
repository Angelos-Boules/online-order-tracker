# Buy-N-Track Order Tracking Simulator

To run:
  1. cdk bootstrap (only need to do once)
  2. cdk deploy

To destroy/clean up resources:
  1. cdk destroy

## Notable Files
- *stack.py* contains the actual stack 
- *lambda_code/order_handler.py* contains the lambda function to handle API requests
- *web/src* contains source files for React application
- *web/dist* is compiled files (which is hosted on S3 once the stack is deployed)
  - To obtain an updated dist/:
  1. cd web
  2. npm run build
