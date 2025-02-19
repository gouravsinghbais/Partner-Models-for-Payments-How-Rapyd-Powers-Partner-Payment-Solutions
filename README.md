# Partner Models for Payments: How Rapyd Powers Partner Payment Solutions
Learn how you can implement the partner payment solution for your SaaS and marketplace business. 

## What do you need to start?

- Rapyd Account (https://dashboard.rapyd.net/sign-up)
- Python>=3.8

## How to run a sample application?

- Log in to your Rapyd account
- Make sure you are using the panel in "sandbox" mode (switch in the bottom left part of the panel)
- Go to the "Developers" tab. You will find your API keys there. Copy them to the version of your sample application of your choice
- Go to the "Webhooks" tab and enter the URL where the application listens for events. By default it is "https://{YOUR_BASE_URL}/api/webhook" and mark which events should be reported to your app
- Run the version of the application of your choice

## How to run this sample Python application?

- open a command prompt and run the `merchant_rapyd_app.py` file with command `uvicorn merchant_repyd_app:app --host 0.0.0.0 --port 8083 --reload`.
- Turn on your browser and go to "http://localhost:8083"
- you can also use thes set of commands to test the application with terminal:

    ```
    curl -X POST "http://localhost:8000/merchant/register?name=JohnDoe"
    curl -X POST "http://localhost:8000/merchant/{merchant_id}/add_product?name=TestProduct&price=100"
    curl -X POST "http://localhost:8000/pay/{product_id}"
    curl -X POST "http://localhost:8000/merchant/{merchant_id}/payout"
    ```

