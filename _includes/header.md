*Total length:* <span id="total-length"></span>
*Vertical range:* <span id="vertical-range"></span>

* [Browse or edit survey data](https://github.com/mshinwell/loser-ng/tree/master/{{ page.dir }})

* [Edit this page](https://github.com/mshinwell/loser-ng/edit/master/{{ page.path }})

<script>
var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    var caves = JSON.parse(this.responseText);
    var cave = caves["cave"];
    document.getElementById("total-length").innerHTML =
      cave["total-length"]
    document.getElementById("vertical-range").innerHTML =
      cave["vertical-range"]
  } else {
    document.getElementById("total-length").innerHTML =
      "(unavailable)"
    document.getElementById("vertical-range").innerHTML =
      "(unavailable)"
  }
};
xmlhttp.open("GET", "cave.json", true);
xmlhttp.send();
</script>
