from __future__ import print_function, division, absolute_import
from cu2qu import fonts_to_quadratic
from cu2qu.geometry import (
    cubic_approx_spline, curve_spline_dist, Point as CPoint)
from defcon import Font, Glyph
from ufoLib.pointPen import AbstractPointPen
from robofab.pens.reverseContourPointPen import ReverseContourPointPen
import sys
import os
import shutil


# Maximum number of quadratic sub-segments approximating a cubic bezier
MAX_N = 10

# Maximum distance between cubic curve and quadratic approximation
MAX_ERR = 1.0

# print out the defect of approximation
DEBUG = False

# remove overlaps before converting outlines to TT
DO_MERGE_CONTOURS = False

# set path direction to TrueType (clockwise)
DO_SET_TT_DIRECTION = True


class Cu2QuPen(AbstractPointPen):
    def __init__(self, otherPointPen, max_n=MAX_N, max_err=MAX_ERR,
                 verbose=False):
        self.pen = otherPointPen
        self.max_n = max_n
        self.max_err = max_err
        self.verbose = verbose
        self.currentPath = None

    def beginPath(self):
        """Start a new sub path."""
        assert self.currentPath is None
        self.currentPath = []

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 **kwargs):
        """Add a point to the current sub-path."""
        self.currentPath.append([pt, segmentType, smooth, name, kwargs])

    def endPath(self):
        """End the current sub path."""
        assert self.currentPath is not None
        points = list(self.currentPath)
        self._flushContour(points)
        self.currentPath = None

    def addComponent(self, baseGlyphName, transformation):
        """Add a sub glyph (Note: components are not filtered)"""
        assert self.currentPath is None
        self.pen.addComponent(baseGlyphName, transformation)

    def _flushContour(self, points):
        assert len(points) >= 1
        if len(points) == 1:
            # anchor point, skip
            self._drawPoints(points)
            return
        segments = self._pointsToSegments(points)
        newSegments = []
        prevSegment = segments[-1]
        for i, segment in enumerate(segments):
            prevOnCurve = prevSegment[-1][0]
            onCurve, segmentType, smooth, name, kwargs = segment[-1]
            if segmentType == 'curve':
                assert len(segment) == 3
                cubic = [prevOnCurve, segment[0][0], segment[1][0], onCurve]
                quad, err = curve_to_quadratic(cubic, self.max_n, self.max_err)
                if self.verbose:
                    print(i, err)
                quadSegment = []
                for pt in quad[1:-1]:
                    quadSegment.append([
                        [int(round(i)) for i in pt], None, None, None, {}])
                quadSegment.append((onCurve, "qcurve", smooth, name, kwargs))
                newSegments.append(quadSegment)
            else:
                newSegments.append(segment)
            prevSegment = segment
        points = self._segmentsToPoints(newSegments)
        self._drawPoints(points)

    def _pointsToSegments(self, points):
        firstSegmentType = points[0][1]
        if firstSegmentType != "move":
            # closed contour: locate the first on-curve point, and rotate
            # the point list so that it ends with an on-curve point.
            firstOnCurve = None
            for i, (pt, segmentType, smooth, name, kwargs) \
                    in enumerate(points):
                if segmentType is not None:
                    firstOnCurve = i
                    break
            if firstOnCurve is None:
                # Special case for quadratics: a contour with no on-curve
                # points. Add a "None" point. (See also the Pen protocol's
                # qCurveTo() method and fontTools.pens.basePen.py.)
                points.append((None, "qcurve", None, None, None))
            else:
                points = points[firstOnCurve+1:] + points[:firstOnCurve+1]
        segments = []
        currentSegment = []
        for pt, segmentType, smooth, name, kwargs in points:
            currentSegment.append([pt, segmentType, smooth, name, kwargs])
            if segmentType is None:
                continue
            segments.append(currentSegment)
            currentSegment = []
        return segments

    def _segmentsToPoints(self, segments):
        points = []
        for segment in segments:
            for point in segment:
                points.append(point)
        # restore the original starting point
        points = points[-1:] + points[:-1]
        return points

    def _drawPoints(self, points):
        self.pen.beginPath()
        for pt, segmentType, smooth, name, kwargs in points:
            self.pen.addPoint(pt, segmentType, smooth, name, **kwargs)
        self.pen.endPath()


def curve_to_quadratic(curve, max_n, max_err):
    """ Return a quadratic spline approximating this cubic bezier, and
    the error of approximation.
    """
    assert len(curve) == 4
    spline, error = None, None
    curve = [CPoint(pt) for pt in curve]
    for n in range(1, max_n + 1):
        spline = cubic_approx_spline(curve, n)
        if spline:
            error = curve_spline_dist(curve, spline)
            if error <= max_err:
                break
    assert spline is not None
    return spline, error


def glyph_to_quadratic(glyph, max_n, max_err, correctDirection=True,
                       verbose=False):
    """ Convert the glyph outline to TrueType quadratic splines. """
    new = Glyph()
    writerPen = new.getPointPen()
    cu2quPen = Cu2QuPen(writerPen, max_n, max_err, verbose)
    if correctDirection:
        reversePen = ReverseContourPointPen(cu2quPen)
        glyph.drawPoints(reversePen)
    else:
        glyph.drawPoints(cu2quPen)
    # clear glyph but keep anchors for mark, mkmk features
    glyph.clearContours()
    glyph.clearComponents()
    writerPen = glyph.getPointPen()
    new.drawPoints(writerPen)


def rmtree(path):
    for root, directories, files in os.walk(path):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in directories:
            shutil.rmtree(os.path.join(root, d))


def font_to_quadratic(font, max_n=MAX_N, max_err=MAX_ERR):
    for glyph in font:
        glyph_to_quadratic(glyph, max_n=MAX_N, max_err=MAX_ERR)


def convert_to_quadratic(source, dest, max_err=MAX_ERR):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    font = Font(source)
    font_to_quadratic(font, max_err=max_err)
    font.save(dest, formatVersion=2)


def main():
    if len(sys.argv) < 2:
        print('usage: convert.py Font.ufo [Font_quad.ufo]', file=sys.stderr)
        return 1
    source = sys.argv[1]
    if len(sys.argv) > 3:
        dest = sys.argv[2]
    else:
        source = source[:-1] if source.endswith('/') else source
        dest = os.path.splitext(source)[0] + '_quad.ufo'
    report = convert_to_quadratic(source, dest)
    print(report)


if __name__ == '__main__':
    main()
