# Welcome to gLLM

## Dev instructions

Below are the steps a new developer in the repo should take to setup their dev env

#### `Src/` - The main application logic

- All packages are managed with uv, so check the docs if you are not familiar with it.
- running `uv` in your terminal will show you the options uv offers. Run `uv sync` to install all dependencies after a fresh clone of the project.
- run `uv add <package name here>` to add a new dependency to the project.
- You'll need the proper .env variables for the project to run, so please configure that before running.
- If vLLM, the S3, PostgreSQL are up, then you can run `/src/start.sh` to start the chainlit server and serve the UI.

#### `Data/` - The data layer of the system

- This uses Prisma as on ORM for the PostgreSQL database that we're using.
- Given you have Node.js installed, run `npm install` (inside the `/Data` dir) to get the necessary dependencies for working with prisma.
- Now, you'll need to run a migration, which adds the database schema to the postgres db. You do this with `npx prisma migrate deploy`.
- You should be able to run `npx prisma studio`, which will setup a prisma studio UI on localhost, where you can confirm that your migration was successfull.
- Run a docker compose up on the compose.yaml inside `/Data`(this will get automated in the docker compose of a prod build in the project root)

#### `/vllmconfig` - Running the Server

- The vLLM start script depends on two env variables: `HF_TOKEN` (Huggingface token used to pull the models for vLLM to host and `MODEL`, which is the name of the model you want to pull from Huggingface.
  - NOTE: Some models have caveats. i.e. some of them require you to sign a consent form or depend on different datatypes for their weights.
  - The start script is not exhaustive in its ability to just run any model, so you may need to tweak the flags here and there where needed.
- To run the server, simply run the start.sh script with `./start.sh`. This starts the server and hosts it on port 8001.

