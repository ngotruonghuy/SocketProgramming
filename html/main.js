fetch("files.json")
    .then(function(response){
        return response.json();
    })
    .then(function(data){
        console.log(data['files.html']);
        var myTable = document.getElementById('myTable');
        var myTitle = document.getElementById('myTitle');
       var flag = 0;
        for (var i in data){
            if (flag == 0){
                var pos = data[i]['path'].lastIndexOf('/');
                var s = data[i]['path'].substr(0,pos)
                myTitle.innerHTML = 'Index of '+s;
                var pos1 = s.lastIndexOf('/');
                row = myTable.insertRow();
                cell = row.insertCell();
                cell.innerHTML = '<a class="folder" href="'+s.substr(0,pos1)+'" >'+'Parent directory</a>';
                flag = 1;
            }
            var row1 = myTable.insertRow();
            for (var key in data[i]){
                var cell1 = row1.insertCell();
                if (key == 'path'){
                    if (i.indexOf('.') == -1){
                        cell1.innerHTML = '<a class="folder" href="'+data[i][key]+'" >'+i+' (folder)</a>';
                    }
                    else{
                        cell1.innerHTML = '<a href="'+data[i][key]+'" download>'+i+'</a>';
                    }
                }
                else{
                    cell1.innerHTML = data[i][key];
                }
            }
        }
    });