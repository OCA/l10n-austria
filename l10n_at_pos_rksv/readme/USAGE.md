Once the POS is configured and assigned, every receipt closed at checkout is
automatically signed and the resulting QR code is printed at the bottom of the
receipt. Special receipts are produced when needed:

- **Startbeleg** – the very first signed receipt of a POS, stamped with the
  marker `STARTBELEG` on the printed receipt.
- **Nullbeleg** – manually triggered via the *Create Zero-Receipt* button on
  the POS configuration; printed with `NULLBELEG`.
- **Monatsbeleg / Jahresbeleg** – RKSV par. 8: a daily cron creates the signed
  zero receipt for every month end, i.e. on the first run of the new month, for
  every active POS without an open session (not in the month of the start
  receipt). It is printed with `MONATSBELEG`. Limits: only the last ended month is
  created, missed months are not back-filled; a POS whose session is open at the
  time of the cron run is skipped until the next run. The Monatsbeleg of December (created
  in January) is the Jahresbeleg and is additionally printed with `JAHRESBELEG`;
  there is no separate year receipt. Start receipt and Jahresbeleg are checked
  automatically after creation. This is only a structure check of the signature
  (JWS well formed, equal to the QR code); it is NOT the full check of RKSV par. 6
  para. 4, the turnover counter is not decrypted.
- **Storno** – cancellation of a previous receipt, printed with `STORNO`.

Cancelled orders consume a receipt number at creation. To keep the receipt
range gapless, they are signed as zeroed receipts (`NULLBELEG`); orders
without any payment have their lines zeroed first. This signing runs right
after a session is closed (triggered asynchronously) and additionally once a
day via cron; a POS with an open session is skipped. Signed orders are
protected against concurrent cancel requests overwriting their state or name.

The list and form views of *Point of Sale > Orders > Orders* expose the RKSV
fields (`a.sign Type`, `a.sign State`, `a.sign Sequence`, `a.sign Counter`,
`a.sign DEP`, `a.sign QR-Code`) for auditing and exporting the DEP.

The *Export DEP* button on the POS configuration downloads the DEP of the POS
as JSON file.

Printable PDF reports are available for the certificate and the POS
configuration via the *Print* menu of the corresponding form.
