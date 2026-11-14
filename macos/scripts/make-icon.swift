import AppKit
let output = CommandLine.arguments[1]
try FileManager.default.createDirectory(atPath:output,withIntermediateDirectories:true)
for size in [16,32,128,256,512] {
    for scale in [1,2] {
        let pixels = size * scale
        let image = NSImage(size:NSSize(width:pixels,height:pixels))
        image.lockFocus()
        let p = CGFloat(pixels)
        NSColor(red:0.16,green:0.40,blue:0.34,alpha:1).setFill()
        NSBezierPath(roundedRect:NSRect(x:p*0.05,y:p*0.05,width:p*0.9,height:p*0.9),xRadius:p*0.21,yRadius:p*0.21).fill()
        NSColor(red:0.96,green:0.96,blue:0.90,alpha:1).setFill()
        NSBezierPath(roundedRect:NSRect(x:p*0.23,y:p*0.19,width:p*0.54,height:p*0.64),xRadius:p*0.07,yRadius:p*0.07).fill()
        NSColor(red:0.16,green:0.40,blue:0.34,alpha:1).setStroke()
        let check = NSBezierPath(); check.lineWidth = p*0.058; check.lineCapStyle = .round; check.lineJoinStyle = .round
        check.move(to:NSPoint(x:p*0.35,y:p*0.51)); check.line(to:NSPoint(x:p*0.46,y:p*0.40)); check.line(to:NSPoint(x:p*0.66,y:p*0.62)); check.stroke()
        image.unlockFocus()
        let bitmap = NSBitmapImageRep(data:image.tiffRepresentation!)!
        let name = "icon_\(size)x\(size)" + (scale == 2 ? "@2x" : "") + ".png"
        try bitmap.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:output).appendingPathComponent(name))
    }
}
