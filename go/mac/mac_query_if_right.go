package main

import (
	"fmt"
	"log"
	"os"

	"github.com/mikepb/go-serial"
)

func main() {

	var CheckPort string
	CheckPort = os.Args[1]

	options := serial.RawOptions
	options.BitRate = 115200
	p, err := options.Open(CheckPort)
	if err != nil {
		fmt.Println("The port can't be connect!!!")
		log.Panic(err)
	}

	defer p.Close()
}
