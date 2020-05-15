all: 1623.log caves-1623/204/204.json

1623.log: 1623.svx
	cavern --log 1623

caves-1623/204/204.json:
	cd caves-1623/204 && cavern --log 204
	echo '{"1623_204": {' > $@
	cat 1623.log \
	  | grep "Total length of survey legs" \
	  | cut -d '=' -f 2 \
	  | awk '{print $$1}' \
	  | sed 's/^ *//' \
	  | sed 's/^/  "total-length":"/' \
	  | sed 's/$$/",/' \
	  >> $@
	cat 1623.log \
	  | grep "Vertical range" \
	  | cut -d '=' -f 2 \
	  | awk '{print $$1}' \
	  | sed 's/^ *//' \
	  | sed 's/^/  "vertical-range":"/' \
	  | sed 's/$$/",/' \
	  >> $@
	echo ' }' >> $@
	echo '}' >> $@