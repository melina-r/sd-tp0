package main

import (
	"context"
	"errors"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	client "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

func loadConfig() (client.ClientConfig, error) {
	val, err := strconv.ParseUint(os.Getenv("AGENCY_ID"), 10, 32)
	if err != nil {
		return client.ClientConfig{}, errors.New("AGENCY_ID environment variable is required")
	}
	agencyId := uint32(val)

	serverHost := os.Getenv("SERVER_HOST")
	if serverHost == "" {
		return client.ClientConfig{}, errors.New("SERVER_HOST environment variable is required")
	}

	serverPort := os.Getenv("SERVER_PORT")
	if serverPort == "" {
		return client.ClientConfig{}, errors.New("SERVER_PORT environment variable is required")
	}

	batchSize, err := strconv.ParseUint(os.Getenv("BATCH_SIZE"), 10, 32)
	if err != nil {
		return client.ClientConfig{}, errors.New("BATCH_SIZE environment variable is required")
	}

	inputFilePath := os.Getenv("INPUT_FILE")
	if inputFilePath == "" {
		return client.ClientConfig{}, errors.New("INPUT_FILE environment variable is required")
	}

	outputFilePath := os.Getenv("OUTPUT_FILE")
	if outputFilePath == "" {
		return client.ClientConfig{}, errors.New("OUTPUT_FILE environment variable is required")
	}

	return client.ClientConfig{
		ServerHost:     serverHost,
		ServerPort:     serverPort,
		AgencyId:       agencyId,
		BatchSize:      int(batchSize),
		InputFilePath:  inputFilePath,
		OutputFilePath: outputFilePath,
	}, nil
}


func run() int {
	config, err := loadConfig()
	if err != nil {
		logger.Error("load-config", logger.Fail, "err", err)
		return 1
	}

	// Crear contexto que se cancela al recibir SIGTERM o SIGINT
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	client, err := client.NewClient(config)
	if err != nil {
		logger.Error("client-new", logger.Fail, "err", err)
		return 1
	}

	// Canal para recibir el resultado del cliente
	done := make(chan error, 1)
	go func() {
		done <- client.Run()
	}()

	select {
	case <-ctx.Done():
		logger.Info("graceful-shutdown", logger.InProgress)
		client.Close() // Cerrar la conexión TCP desbloquea las I/O pendientes
		<-done        // Esperar a que termine la gorutina
		logger.Info("graceful-shutdown", logger.Success)
		return 0
	case err := <-done:
		if err != nil {
			logger.Error("client-run", logger.Fail, "err", err)
			return 1
		}
		return 0
	}
}

func main() {
	os.Exit(run())
}