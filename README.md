# TechConf Registration Website

## Project Overview
The TechConf website allows attendees to register for an upcoming conference. Administrators can also view the list of attendees and notify all attendees via a personalized email message.

The application is currently working but the following pain points have triggered the need for migration to Azure:
 - The web application is not scalable to handle user load at peak
 - When the admin sends out notifications, it's currently taking a long time because it's looping through all attendees, resulting in some HTTP timeout exceptions
 - The current architecture is not cost-effective 

In this project, you are tasked to do the following:
- Migrate and deploy the pre-existing web app to an Azure App Service
- Migrate a PostgreSQL database backup to an Azure Postgres database instance
- Refactor the notification logic to an Azure Function via a service bus queue message

## Dependencies

You will need to install the following locally:
- [Postgres](https://www.postgresql.org/download/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Azure Function tools V3](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
- [Azure Tools for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack)

## Project Instructions

### Part 1: Create Azure Resources and Deploy Web App
1. Create a Resource group
2. Create an Azure Postgres Database single server
   - Add a new database `techconfdb`
   - Allow all IPs to connect to database server
   - Restore the database with the backup located in the data folder
3. Create a Service Bus resource with a `notificationqueue` that will be used to communicate between the web and the function
   - Open the web folder and update the following in the `config.py` file
      - `POSTGRES_URL`
      - `POSTGRES_USER`
      - `POSTGRES_PW`
      - `POSTGRES_DB`
      - `SERVICE_BUS_CONNECTION_STRING`
4. Create App Service plan
5. Create a storage account
6. Deploy the web app

### Part 2: Create and Publish Azure Function
1. Create an Azure Function in the `function` folder that is triggered by the service bus queue created in Part 1.

      **Note**: Skeleton code has been provided in the **README** file located in the `function` folder. You will need to copy/paste this code into the `__init.py__` file in the `function` folder.
      - The Azure Function should do the following:
         - Process the message which is the `notification_id`
         - Query the database using `psycopg2` library for the given notification to retrieve the subject and message
         - Query the database to retrieve a list of attendees (**email** and **first name**)
         - Loop through each attendee and send a personalized subject message
         - After the notification, update the notification status with the total number of attendees notified
2. Publish the Azure Function

### Part 3: Refactor `routes.py`
1. Refactor the post logic in `web/app/routes.py -> notification()` using servicebus `queue_client`:
   - The notification method on POST should save the notification object and queue the notification id for the function to pick it up
2. Re-deploy the web app to publish changes

## Monthly Cost Analysis
Complete a month cost analysis of each Azure resource to give an estimate total cost using the table below:

| Azure Resource            | Service Tier                      | Monthly Cost                                |
| ------------------------- | --------------------------------- | ------------------------------------------- |
| *App Service Plan*        | B1                                | ~ 13.14 USD per Month (free in first month) |
| *Azure Service Bus*       | Basic                             | ~ 0.05 USD per 1000000 messages             |
| *Azure Postgres Database* | Basic, 1 vCore(s), 5 GB           | ~ 25.32 USD per Month                       |
| *Azure Function App*      | see App Servive Plan              | covered by App Service Plan                 |
| *Azure Storage Account*   | Standard, cold, locally redundant | 0.01 USD per GB                             |
| *Azure Web App*           | see App Service Plan              | covered by App Service Plan                 |

## Architecture Explanation
For the web app I've chosen the B1 tier app service plan. In this scenario I would have gone with the free F1 tier for the web app but for the azure function app with python runtime the B1 app service plan was the minumum requirement. As for the web app anyways an app service plan was required, it made sense to reuse this for the function app. 

In a production context I would still have selected the B1 tier for the app service plan given that the web app will only be viewed by conference attendees and doesn't require heavy computation on the server side and the notfications will only be issued by conference admins and the number of notifications will thus also be limited. 

In general it makes sense to offload the time consuming task of sending notificaitons to a component that is separate from the actual web app. This ways the web app can handle web requests with fast response times. As notifications are only sent from time to time it makes sense to use an azure function to handle these.
