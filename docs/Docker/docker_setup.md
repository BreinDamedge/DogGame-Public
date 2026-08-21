# Docker Setup
1. put dockerignore, dockerfile into the src directory
1. run the build command `docker build -t doggame:latest .`
1. run your docker run command 
    - note: use an absolute path for your corpus directory in the docker run command


```
docker run -d \
    --name DogGame \
    -p <port on host machine>:1234 \
    -v <absolute path on host machine to corpus folder>:/app/Documents \
    doggame:latest
```

something like this

docker run -d --name DogGame -p 1234:1234 -v C:/Users/<you>/DogGame/src/Documents:/app/Documents doggame:latest