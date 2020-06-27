<?php
    include("loader.php");
    $db_con = makeDatabaseConnection();
    $db_con.query("SELECT * form users");
    function login(){
        // log user in 
        $_SESSION["user"] = $user;
    }
    $sc_instance = someClass();
    $sc_instance -> makeDatabaseConnection();

    login();
?>
