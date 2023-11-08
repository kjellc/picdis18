<?php

$lines = file('./regnames18_cowbasic.txt');
$output_file = fopen('./regnames18.txt', 'w');

foreach ($lines as $line) {
    $pattern = '/(?P<name>\w+),(?P<address>\d+)/';
    preg_match($pattern, $line, $matches); // Outputs 1
    $formatted = sprintf("%04X %s", $matches['address'], $matches['name']);
    fwrite($output_file, $formatted."\n");
    echo $formatted."\n";
}
fclose ($output_file);

?>