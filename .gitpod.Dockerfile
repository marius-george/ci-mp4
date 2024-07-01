FROM gitpod/workspace-full:latest

# Add PostgreSQL repository
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y postgresql-12 postgresql-client-12

# Start PostgreSQL service and create a user and database
RUN sudo service postgresql start && \
    sudo -u postgres psql -c "CREATE USER gitpod WITH SUPERUSER PASSWORD 'gitpod';" && \
    sudo -u postgres createdb -O gitpod gitpod

# Expose PostgreSQL port
EXPOSE 5432
