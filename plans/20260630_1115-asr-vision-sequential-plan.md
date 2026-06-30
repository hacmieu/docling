# Plan: ASR → Vision JPG (tuần tự)

## Đã xong

1. [x] ASR ingest doc 991
2. [x] Enrich doc 991
3. [x] Dừng vision batch PDF song song (quota conflict)
4. [x] Retry vision 21 JPG với sleep 45s

## Còn lại

- [ ] Chờ `1115-vision-jpg-batch-retry` hoàn tất
- [ ] Resume vision batch PDF (`0820`) khi quota ổn định
- [ ] Commit code + push develop
