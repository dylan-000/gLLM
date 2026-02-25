# Welcome to gLLM

### Project Structure
```python
.
├── frontend                # UI for the Entry Dashboard
│   ├── public
│   └── src
│       ├── assets
│       ├── components      # React UI Components
│       │   └── ui
│       ├── lib
│       └── pages           # React Page Componenets
├── src
│   ├── Data                # SQLAlch models, DB Session generator, and DTOs
│   │   └── alembic         # Database migration history
│   │       └── versions
│   ├── Prompts             # Prompts, Prompt Templates
│   ├── public              # Chainlit public dir for serving images
│   ├── Routers             # FastApi API Routers
│   └── Services            # Service methods for APIs
├── tests                   # Unit and Integration Tests
└── vllmconfig              # vLLM init script (will be removed later)
```


### Sequential Steps for Running the System
1. Inside `/data`, run `docker compose up` to pull and run the PostgreSQL database container.
2. Still in this directory, run `npm install` to install the Prisma ORM dependencies.
3. You'll need to create a `.env` file of the following format to enable the migrations to connect to your database: `DATABASE_URL= {your postgres connection string here}`
4. You'll need a .env file in the `src/chainlit/` dir of the following schema to enable chainlits interfacing with the ORM:
  ```
  DATABASE_URL=
  BUCKET_NAME=
  APP_AWS_ACCESS_KEY=
  APP_AWS_SECRET_KEY=
  APP_AWS_REGION=
  CHAINLIT_AUTH_SECRET=
  ```
5. You can now run `npx prisma migrate deploy` to apply the schema to your postgres db.
6. Run `npx prisma studio` and navigate to the prisma studio interface to verify that the schema has been applied.
7. For the FastApi services, you'll need the Prisma Client so that they can interface with the ORM and acccess the database. To do this, navigate to the `/Data` dir, and run `npx prisma generate`. This will create a folder in `/src/` that contains the Python Prisma Client code. Any time you create a migration to the database with Prisma, you'll need to also regenerate the client so that it has the updated schema.