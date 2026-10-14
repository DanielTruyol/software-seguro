for i in $(seq 9900 13000); do
hash=$(printf "%d" "$i" | md5sum | awk '{print $1}')
echo "$hash"
done
