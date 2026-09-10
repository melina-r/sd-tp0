package safe_socket

import "io"

// SendAll sends all bytes in the provided slice to the given socket.
// It ensures that all bytes are sent, handling partial sends if necessary.
// If an error occurs during sending, it returns the error.
func SendAll(socket io.Writer, bytes []byte) error {
	totalSent := 0
	for totalSent < len(bytes) {
		n, err := socket.Write(bytes[totalSent:])
		totalSent += n
		if err != nil {
			return err
		}
	}
	return nil
}

// RecvAll receives a specified number of bytes from the given socket.
// It ensures that all requested bytes are received, handling partial reads if necessary.
// If an error occurs during receiving, it returns the error.
func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	totalRead := 0
	for totalRead < size {
		n, err := socket.Read(buff[totalRead:])
		totalRead += n
		if err != nil {
			return nil, err
		}
	}
	return buff, nil
}