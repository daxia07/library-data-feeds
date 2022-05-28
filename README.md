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
```javascript
db.createCollection('books');
db.createCollection('checkouts');
db.createCollection('explore');
db.createCollection('history');
db.createCollection('holds');
db.createCollection('requests');
db.createCollection('reviews');
db.books.createIndex(
  {
      "isbn": 1
  },
  {
      unique: true,
  }
);
db.checkouts.createIndex(
  {
      "account": 1,
      "isbn": 1
  },
  {
      unique: true,
  }
);
db.history.createIndex(
  {
      "account": 1,
      "isbn": 1,
      "returned": 1
  },
  {
      unique: true,
  }
);
db.holds.createIndex(
  {
      "account": 1,
      "isbn": 1
  },
  {
      unique: true,
  }
);


```