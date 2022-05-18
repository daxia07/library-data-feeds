### Backend container app 

### Commands
```bash
docker build -t library-data-feeds .
docker run --name lib-api -p 5000:5000 library-data-feeds
```