<?php
    include("../simple2.php");
    function simpleprint(){
        echo "Just A String Here. Nothing Fancy.";
        try{
            dosomething();
        }
        catch(Exception $e){
        }
    }
    try{
        dosomethingelse();
    }catch(Exception $e){
    }
?>
