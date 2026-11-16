// Helper jaringan: resolve IP publik + info antarmuka.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"time"
)

type out struct {
	Local  []string `json:"local"`
	Public string   `json:"public"`
	Error  string   `json:"error,omitempty"`
}

func main() {
	res := out{Local: []string{}}
	ifaces, err := net.Interfaces()
	if err == nil {
		for _, i := range ifaces {
			addrs, _ := i.Addrs()
			for _, a := range addrs {
				if ipnet, ok := a.(*net.IPNet); ok && ipnet.IP.To4() != nil {
					res.Local = append(res.Local, ipnet.IP.String())
				}
			}
		}
	}
	client := &http.Client{Timeout: 6 * time.Second}
	r, err := client.Get("https://api.ipify.org")
	if err == nil {
		defer r.Body.Close()
		b, _ := io.ReadAll(r.Body)
		res.Public = string(b)
	} else {
		res.Error = err.Error()
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(res); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
