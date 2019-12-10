package main

import (
	"fmt"
	"log"

	"github.com/mikepb/go-serial"
)

func main() {
	ports, err := serial.ListPorts()
	if err != nil {
		log.Panic(err)
	}

	// log.Printf("Found %d ports:\n", len(ports))

	var listPortsOs string
	listPortsOs = "["
	for _, info := range ports {
		listPortsOs += "'" + info.Name() + "', "
	}
	listPortsOs = listPortsOs[:len(listPortsOs)-2] + "]"

	fmt.Println(listPortsOs)
}
