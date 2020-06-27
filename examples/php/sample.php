<?php
    require("simple/simple.php");

    $someCondition = 1;

    function f1(){
        echo "This is just a function";
    }
    try{
        echo "Hi";
    }catch(Exception $e){
    };

    if ($someCondition == 1){
        function f2(){
            echo "This is another function";
    }
        }else{
            function f1(){
                echo "hi";
            }
            echo "This is the else block";
        }
    f2();
    $mysql_handle = mysql_connect("Blah Blah Blah");
    $query_result = mysql_query("SELECT * from users where password=$password")
?>
