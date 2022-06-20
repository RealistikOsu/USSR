package main

import (
	_ "github.com/go-sql-driver/mysql"
	"github.com/jmoiron/sqlx"

	"fmt"
	"log"
	"reflect"
	"sync"
)

// Edit these variables only.
var SQL_HOST = "localhost"
var SQL_USER = "root"
var SQL_PASSWORD = ""
var SQL_PORT = "3306"
var SQL_DATABASE = "ripple"

// statistics variables, dont edit.
var USERS_COUNT = 0

var DB *sqlx.DB

func updateCountry(idx int, usersList []int) {

	log.Println(fmt.Sprintf("[Thread #%d] Starting job...", idx))

	for _, userID := range usersList {
		var country string
		err := DB.Get(&country, "SELECT country FROM users_stats WHERE id = ?", userID)
		if err != nil {
			log.Println(err)
			continue
		}
		if country == "" {
			country = "XX"
		}
		_, err = DB.Exec("UPDATE users SET country = ? WHERE id = ?", country, userID)
		log.Println(fmt.Sprintf("[Thread #%d] Updated user id: %d", idx, userID))
		USERS_COUNT += 1
	}
}

func SplitToChunks(slice interface{}, chunkSize int) interface{} {
	sliceType := reflect.TypeOf(slice)
	sliceVal := reflect.ValueOf(slice)
	length := sliceVal.Len()
	if sliceType.Kind() != reflect.Slice {
		panic("parameter must be []T")
	}
	n := 0
	if length%chunkSize > 0 {
		n = 1
	}
	SST := reflect.MakeSlice(reflect.SliceOf(sliceType), 0, length/chunkSize+n)
	st, ed := 0, 0
	for st < length {
		ed = st + chunkSize
		if ed > length {
			ed = length
		}
		SST = reflect.Append(SST, sliceVal.Slice(st, ed))
		st = ed
	}
	return SST.Interface()
}

func main() {
	log.Println("Starting country field migrator!")

	log.Println("Connecting to database...")
	// initialise db
	dbDSN := fmt.Sprintf("%s:%s@(%s:%s)/%s", SQL_USER, SQL_PASSWORD, SQL_HOST, SQL_PORT, SQL_DATABASE)
	DB = sqlx.MustConnect("mysql", dbDSN+"?parseTime=true&allowNativePasswords=true")
	log.Println("Connection Initialised!")

	var userIDList []int

	log.Println("Fetching user IDs...")
	// get user IDs
	err := DB.Select(&userIDList, "SELECT id FROM users")
	if err != nil {
		panic(err)
	}

	var wg sync.WaitGroup

	// Start threads.
	for index, userChunk := range SplitToChunks(userIDList, 1000).([][]int) {
		wg.Add(1)
		go func(idx int, chunk []int) {
			defer wg.Done()
			updateCountry(idx+1, chunk)
		}(index, userChunk)
	}
	// Wait till all threads are finished.
	wg.Wait()

	log.Println(fmt.Sprintf("[Main] Finished. Initial Users: %d // Users updated: %d", len(userIDList), USERS_COUNT))
}
