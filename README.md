### Library backend services

### Pre-requests
1. Create splash instance to log in with JS on heroku
2. Define URL

### Backend container app 

### Commands
Build container
```bash
docker build -t library-data-feeds .
docker run --name lib-api -p 5000:5000 library-data-feeds
```
Deploy container
```bash
heroku create pd-lib-api
heroku container:login
heroku container:push web --app pd-lib-api
heroku container:release web --app pd-lib-api
heroku logs --tail --app pd-lib-api
```

### Setup database
```bash
db.createCollection('books');
db.createCollection('checkouts');
db.createCollection('explore');
db.createCollection('history');
db.createCollection('holds');
db.createCollection('requests');
db.createCollection('reviews');
```